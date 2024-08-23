bl_info = {
    "name": "Optimus",
    "blender": (2, 82, 0),  # Minimum Blender version
    "category": "Object",
}

import bpy
import os
from bpy.props import IntProperty, FloatProperty, PointerProperty
from mathutils import Matrix, Vector

class OBJECT_OT_create_camera(bpy.types.Operator):
    bl_idname = "object.create_camera"
    bl_label = "Create Camera"
    bl_options = {'REGISTER', 'UNDO'}

    resolution: IntProperty(
        name="Resolution",
        description="Resolution of the camera image",
        default=1080,
        min=1
    )
    distance: FloatProperty(
        name="Distance",
        description="Distance of the camera from the object",
        default=5.0,
        min=0.0
    )
    orthographic_scale: FloatProperty(
        name="Orthographic Scale",
        description="Orthographic scale of the camera",
        default=5.0,
        min=0.0
    )
    multiple_angles: bpy.props.BoolProperty(
        name="Multiple Angles",
        description="Render the object from multiple angles",
        default=False
    )

    def execute(self, context):
        obj = context.active_object
        if obj is None:
            self.report({'ERROR'}, "No object selected.")
            return {'CANCELLED'}

        cameras = []
        filepaths = []

        def create_camera_and_render(angle_offset=0):
            bpy.ops.object.camera_add()
            camera = context.active_object
            cameras.append(camera)

            camera.data.type = 'ORTHO'
            camera.data.ortho_scale = self.orthographic_scale
            camera.data.sensor_fit = 'HORIZONTAL'

            direction = obj.matrix_world.to_quaternion() @ Vector((0, -1, 0))
            camera.location = obj.location + direction * self.distance

            rotation_matrix = Matrix.Rotation(angle_offset, 4, 'Z')
            camera.location = rotation_matrix @ (camera.location - obj.location) + obj.location

            look_at = obj.location - camera.location
            camera.rotation_euler = look_at.to_track_quat('Z', 'Y').to_euler()

            camera.rotation_euler.rotate_axis('Y', 3.14159)

            scene = context.scene
            scene.camera = camera
            scene.render.resolution_x = self.resolution
            scene.render.resolution_y = self.resolution

            output_dir = bpy.path.abspath("//")
            filepath = os.path.join(output_dir, f"rendered_image_{angle_offset}.png")
            filepaths.append(filepath)

            scene.render.filepath = filepath
            bpy.ops.render.render(write_still=True)

        create_camera_and_render()

        if self.multiple_angles:
            create_camera_and_render(angle_offset=1.5708)
            create_camera_and_render(angle_offset=3.14159)

        for i, filepath in enumerate(filepaths):
            bpy.ops.mesh.primitive_plane_add(size=self.orthographic_scale)
            plane = context.active_object

            if i == 0 and self.multiple_angles:
                plane.location += cameras[i].matrix_world.to_quaternion() @ Vector((0, 0, -0.001))

            plane.location = obj.location
            plane.rotation_euler = cameras[i].rotation_euler

            mat = bpy.data.materials.new(name=f"RenderedMaterial_{i}")
            plane.data.materials.append(mat)
            mat.use_nodes = True
            bsdf = mat.node_tree.nodes.get('Principled BSDF')
            tex_image = mat.node_tree.nodes.new('ShaderNodeTexImage')

            if os.path.exists(filepath):
                tex_image.image = bpy.data.images.load(filepath)
                mat.node_tree.links.new(bsdf.inputs['Base Color'], tex_image.outputs['Color'])
                mat.node_tree.links.new(bsdf.inputs['Alpha'], tex_image.outputs['Alpha'])
                mat.blend_method = 'BLEND'
            else:
                self.report({'ERROR'}, f"Failed to save or load the image from {filepath}.")
                return {'CANCELLED'}

        for camera in cameras:
            bpy.data.objects.remove(camera, do_unlink=True)

        self.report({'INFO'}, f"Camera(s) created, images rendered, and textures applied to planes.")
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

def register():
    bpy.utils.register_class(OBJECT_OT_create_camera)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_create_camera)

if __name__ == "__main__":
    register()

class AddDecimateModifierOperator(bpy.types.Operator):
    bl_idname = "object.add_decimate_modifier"
    bl_label = "Decimate All Objects"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        decimate_ratio = scene.decimate_ratio

        selected_collection = scene.selected_collection
        objects = selected_collection.objects if selected_collection else bpy.data.objects
        count = 0

        for obj in objects:
            if obj.type == 'MESH':
                modifier = next((mod for mod in obj.modifiers if mod.type == 'DECIMATE'), None)
                if not modifier:
                    modifier = obj.modifiers.new(name="Decimate", type='DECIMATE')

                modifier.ratio = decimate_ratio
                count += 1

        self.report({'INFO'}, f"Added Decimate modifier to {count} objects with ratio {decimate_ratio}.")
        return {'FINISHED'}

class OBJECT_PT_manage_materials_panel(bpy.types.Panel):
    bl_label = "Manage Materials and Modifiers"
    bl_idname = "OBJECT_PT_manage_materials_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Optimus'
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.label(text="Decimate All Objects:")
        layout.prop(scene, "decimate_ratio", text="Decimate Ratio")
        
        layout.prop(scene, "selected_collection", text="Collection")
        layout.operator(AddDecimateModifierOperator.bl_idname, text="Decimate All Objects")

        layout.separator()

        layout.operator(DeleteUnusedMaterialsOperator.bl_idname, text="Delete Unused Materials")
        layout.operator(PurgeUnusedDataOperator.bl_idname, text="Purge Unused Data")

        layout.separator()

        layout.label(text="Camera Culling Decimation:")
        layout.prop(scene, "culling_distance_threshold", text="Distance Threshold")
        layout.prop(scene, "decimate_per_meter", text="Decimate per Meter")
        layout.prop(scene, "minimum_decimation_ratio", text="Minimum Decimation")
        layout.operator(CameraCullingDecimateOperator.bl_idname, text="Camera Culling Decimation")

        layout.separator()

        layout.operator(EnablePersistentDataOperator.bl_idname, text="Enable Persistent Data")

class DeleteUnusedMaterialsOperator(bpy.types.Operator):
    bl_idname = "object.delete_unused_materials"
    bl_label = "Delete Unused Materials"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        all_materials = bpy.data.materials
        deleted_count = 0
        for mat in all_materials:
            assigned_objects = [obj.name for obj in bpy.data.objects if obj.type == 'MESH' and any(slot.material == mat for slot in obj.material_slots)]
            
            if assigned_objects:
                objects_str = ", ".join(assigned_objects)
                self.report({'INFO'}, f"Material: {mat.name}, Users: {mat.users}, Assigned to: {objects_str}")
            else:
                material_name = mat.name
                bpy.data.materials.remove(mat)
                self.report({'INFO'}, f"Deleted Material: {material_name} (not assigned to any objects)")
                deleted_count += 1

        self.report({'INFO'}, f"Materials search completed. Deleted {deleted_count} unused materials.")
        return {'FINISHED'}

class PurgeUnusedDataOperator(bpy.types.Operator):
    bl_idname = "object.purge_unused_data"
    bl_label = "Purge Unused Data"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.outliner.orphans_purge(do_recursive=True)
        self.report({'INFO'}, "Purged all unused data.")
        return {'FINISHED'}

class CameraCullingDecimateOperator(bpy.types.Operator):
    bl_idname = "object.camera_culling_decimate"
    bl_label = "Camera Culling Decimation"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        selected_collection = scene.selected_collection
        distance_threshold = scene.culling_distance_threshold
        decimate_per_meter = scene.decimate_per_meter
        minimum_decimation = scene.minimum_decimation_ratio

        objects = selected_collection.objects if selected_collection else bpy.data.objects
        active_camera = scene.camera
        count = 0

        for obj in objects:
            if obj.type == 'MESH':
                modifier = next((mod for mod in obj.modifiers if mod.type == 'DECIMATE'), None)
                if not modifier:
                    modifier = obj.modifiers.new(name="Decimate", type='DECIMATE')

                if active_camera:
                    distance = (active_camera.location - obj.location).length
                    self.report({'INFO'}, f"Object: {obj.name}, Distance from Camera: {distance:.2f} meters")

                    if distance <= distance_threshold:
                        modifier.ratio = 1.0
                        self.report({'INFO'}, f"Object {obj.name} is within the distance threshold, no decimation applied.")
                    else:
                        extra_distance = distance - distance_threshold
                        modifier.ratio = max(minimum_decimation, 1.0 - extra_distance * decimate_per_meter)
                        self.report({'INFO'}, f"Decimation ratio for {obj.name}: {modifier.ratio:.2f}")

                count += 1

        self.report({'INFO'}, f"Applied Camera Culling Decimation to {count} objects.")
        return {'FINISHED'}

class EnablePersistentDataOperator(bpy.types.Operator):
    bl_idname = "object.enable_persistent_data"
    bl_label = "Enable Persistent Data"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        context.scene.render.use_persistent_data = True
        self.report({'INFO'}, "Persistent data enabled.")
        return {'FINISHED'}

def register_keymaps():
    wm = bpy.context.window_manager
    keyconfigs = wm.keyconfigs
    addon_keymap = keyconfigs.addon.keymaps.new(name='3D View', space_type='VIEW_3D')
    kmi = addon_keymap.keymap_items.new(OBJECT_OT_create_camera.bl_idname, 'N', 'PRESS', shift=True)
    return addon_keymap, kmi

def unregister_keymaps(km, kmi):
    if km and kmi:
        km.keymap_items.remove(kmi)
        bpy.context.window_manager.keyconfigs.addon.keymaps.remove(km)

def register():
    bpy.utils.register_class(OBJECT_OT_create_camera)
    bpy.utils.register_class(OBJECT_PT_manage_materials_panel)
    bpy.utils.register_class(DeleteUnusedMaterialsOperator)
    bpy.utils.register_class(PurgeUnusedDataOperator)
    bpy.utils.register_class(AddDecimateModifierOperator)
    bpy.utils.register_class(CameraCullingDecimateOperator)
    bpy.utils.register_class(EnablePersistentDataOperator)

    register_keymaps()

    bpy.types.Scene.decimate_ratio = FloatProperty(
        name="Decimate Ratio",
        description="Decimation ratio for all objects",
        default=0.5,
        min=0.0,
        max=1.0
    )

    bpy.types.Scene.culling_distance_threshold = FloatProperty(
        name="Distance Threshold",
        description="Distance threshold for camera culling decimation",
        default=10.0,
        min=0.0
    )

    bpy.types.Scene.decimate_per_meter = FloatProperty(
        name="Decimate per Meter",
        description="Decimate ratio decrease per meter beyond the threshold",
        default=0.1,
        min=0.0
    )

    bpy.types.Scene.minimum_decimation_ratio = FloatProperty(
        name="Minimum Decimation",
        description="Minimum decimation ratio",
        default=0.1,
        min=0.0,
        max=1.0
    )

    bpy.types.Scene.selected_collection = PointerProperty(
        name="Selected Collection",
        type=bpy.types.Collection,
        description="Collection to apply operations on"
    )

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_create_camera)
    bpy.utils.unregister_class(OBJECT_PT_manage_materials_panel)
    bpy.utils.unregister_class(DeleteUnusedMaterialsOperator)
    bpy.utils.unregister_class(PurgeUnusedDataOperator)
    bpy.utils.unregister_class(AddDecimateModifierOperator)
    bpy.utils.unregister_class(CameraCullingDecimateOperator)
    bpy.utils.unregister_class(EnablePersistentDataOperator)

    unregister_keymaps(*register_keymaps())

    del bpy.types.Scene.decimate_ratio
    del bpy.types.Scene.culling_distance_threshold
    del bpy.types.Scene.decimate_per_meter
    del bpy.types.Scene.minimum_decimation_ratio
    del bpy.types.Scene.selected_collection

if __name__ == "__main__":
    register()
