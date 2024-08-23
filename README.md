# Optimus Blender Addon

**Optimus** is a blender plug-in that compacts simple to use optimizations into a single button

## Features

### 1. Create Camera and Render Textured Planes

This feature allows you to create an orthographic camera aligned with the selected object, render the object, and automatically create a plane with the rendered texture applied to it. This is especially useful for optimizing scenes by converting complex objects into textured planes.

- **Resolution**: Set the resolution of the rendered image.
- **Distance**: Define the distance of the camera from the object.
- **Orthographic Scale**: Set the orthographic scale of the camera.
- **Multiple Angles**: When enabled, the addon will create three cameras at 90-degree intervals around the object, render each view, and place corresponding textured planes facing the object from different angles.

#### How it works
- The camera is positioned at a user-defined distance and aligned to face the object.
- If "Multiple Angles" is enabled, two additional cameras are created, rotated around the object's Z-axis by 90 and 180 degrees.
- After rendering the object, the addon creates planes and applies the rendered textures to them. The first plane is positioned 1mm closer to the camera to avoid overlap if multiple planes are created.
- Once the render and plane creation are complete, all temporary cameras are deleted from the scene.

### 2. Decimate All Objects

This feature allows you to quickly apply a decimate modifier to all objects in a selected collection or throughout the entire scene, reducing the polygon count and optimizing performance.

- **Decimate Ratio**: Set the decimation ratio to apply to all objects.
- **Collection**: Select the collection to apply the decimation to, or leave it empty to apply to all objects in the scene.

#### How it works
- The addon iterates through all objects in the specified collection or scene.
- If an object is a mesh and doesn’t already have a decimate modifier, one is added, and the specified decimation ratio is applied.
- The operation can be undone, allowing for easy experimentation.

### 3. Delete Unused Materials

Automatically removes all materials that are not assigned to any objects in the scene, helping to keep your project clean and organized.

#### How it works
- The addon checks all materials in the scene.
- Materials that are not used by any object are deleted, freeing up memory and decluttering your material list.

### 4. Purge Unused Data

This feature purges all unused data blocks in your Blender file, including materials, meshes, textures, and other assets that are no longer linked to any object.

#### How it works
- The addon calls Blender’s internal `orphans_purge` function to remove all data blocks that have zero users.

### 5. Camera Culling Decimation

Decimate objects in the scene based on their distance from the active camera. Objects closer to the camera remain high-quality, while objects further away are decimated, optimizing performance without sacrificing visual fidelity.

- **Distance Threshold**: Set the distance threshold for when decimation should start.
- **Decimate per Meter**: Define how much decimation should increase per meter beyond the threshold.
- **Minimum Decimation Ratio**: Set the minimum ratio of decimation to be applied to distant objects.

#### How it works
- The addon calculates the distance of each object from the active camera.
- Objects within the distance threshold are not decimated.
- Objects beyond the threshold are decimated incrementally based on their distance from the camera, with a cap at the minimum decimation ratio.

### 6. Enable Persistent Data

This feature enables Blender's persistent data option, which can significantly speed up rendering by reusing data from previous frames.

#### How it works
- The addon simply toggles Blender's `use_persistent_data` option in the render settings, making it easier to enable this feature without diving into the settings manually.


