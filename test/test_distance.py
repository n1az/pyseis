import rasterio
from scipy.ndimage import gaussian_filter
import numpy as np
import matplotlib.pyplot as plt
from rasterio.plot import show
from rasterio.transform import from_origin
import json
import os
import sys

# Add the parent directory to the path to import custom functions
script_directory = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(script_directory, '..'))

from bin import spatial_distance

# Load example DEM from JSON file
with open('data/volcano.json', 'r') as json_file:
    volcano_data = json.load(json_file)

# Convert the loaded data to a numpy array
volcano_array = np.array(volcano_data)

# Create a rasterio dataset from the volcano data
height, width = volcano_array.shape
transform = from_origin(0, 0, 10, 10)  # Assuming 1 unit resolution

with rasterio.open(
    'volcano.tif',
    'w',
    driver='GTiff',
    height=height,
    width=width,
    count=1,
    dtype=volcano_array.dtype,
    crs='+proj=latlong',
    transform=transform,
) as dst:
    dst.write(volcano_array, 1)

# Open the created raster
dem = rasterio.open('volcano.tif')

# Scale and shift the DEM
dem_array = dem.read(1) * 10
new_transform = from_origin(510, 510 + height * 10, 10, 10)

with rasterio.open(
    'volcano_scaled.tif',
    'w',
    driver='GTiff',
    height=height,
    width=width,
    count=1,
    dtype=dem_array.dtype,
    crs='+proj=latlong',
    transform=new_transform,
) as dst:
    dst.write(dem_array, 1)

# Open the scaled raster
dem = rasterio.open('volcano_scaled.tif')

# Define example stations
stations = np.array([[200, 220], [700, 700]])

# Plot example data
fig, ax = plt.subplots(figsize=(10, 8))
show(dem, ax=ax)
ax.scatter(stations[:, 0], stations[:, 1], c='red', s=50)
ax.set_title('DEM with Stations')
plt.show()

# Calculate distance matrices and station distances
D = spatial_distance.spatial_distance(stations=stations, dem=dem)

# Plot distance map for station 1
fig, ax = plt.subplots(figsize=(10, 8))
im = ax.imshow(D['maps'][0]['val'], extent=D['maps'][0]['ext'], cmap='viridis')
ax.set_title('Distance Map for Station 1')
plt.colorbar(im, ax=ax, label='Distance')
plt.show()

# Show station distance matrix
print("Station Distance Matrix:")
print(D['matrix'])

# Calculate with AOI and in verbose mode
D_aoi = spatial_distance.spatial_distance(stations=stations, dem=dem, verbose=True, aoi=[0, 200, 0, 200])

# Plot distance map for station 2 with AOI
fig, ax = plt.subplots(figsize=(10, 8))
im = ax.imshow(D_aoi['maps'][1]['val'], extent=D_aoi['maps'][1]['ext'], cmap='viridis')
ax.set_title('Distance Map for Station 2 (with AOI)')
plt.colorbar(im, ax=ax, label='Distance')
plt.show()