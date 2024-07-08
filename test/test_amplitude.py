import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm
import rasterio
from rasterio.transform import from_origin
import os
import sys

# Add the parent directory to the path to import custom functions
script_directory = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(script_directory, '..'))

from bin import spatial_amplitude, spatial_distance, spatial_pmax

# Function to create a synthetic DEM and save it to a file
def create_dem(xmin, xmax, ymin, ymax, res, filepath):
    width = int((xmax - xmin) / res[0])
    height = int((ymax - ymin) / res[1])
    print(f"Creating DEM with dimensions: {width}x{height}")
    print(f"DEM extent: ({xmin}, {ymin}) to ({xmax}, {ymax})")
    print(f"Resolution: {res}")
    
    dem = np.zeros((height, width), dtype=np.float32)
    transform = from_origin(xmin, ymax, res[0], res[1])

    # Add some random terrain to make it more realistic
    x = np.linspace(0, 1, width)
    y = np.linspace(0, 1, height)
    X, Y = np.meshgrid(x, y)
    dem = (np.sin(5 * X) * np.cos(5 * Y) + np.random.rand(height, width) * 0.1) * 100

    with rasterio.open(
        filepath, 'w',
        driver='GTiff',
        height=height,
        width=width,
        count=1,
        dtype=dem.dtype,
        crs='+proj=latlong',
        transform=transform,
    ) as dst:
        dst.write(dem, 1)
    
    print(f"DEM created and saved to {filepath}")
    return filepath

# Main code
if __name__ == "__main__":
    # Define station coordinates (in the same coordinate system as the DEM)
    sta = np.array([[25, 25], [75, 75], [50, 90]])  # Adjusted to be within DEM bounds
    sta_ids = ['A', 'B', 'C']

    # Create and save synthetic DEM
    dem_filepath = create_dem(0, 100, 0, 100, res=(1, 1), filepath='synthetic_dem.tif')

    # Read the DEM back in as a rasterio object
    with rasterio.open(dem_filepath) as dem:
        print(f"Loaded DEM bounds: {dem.bounds}")
        print(f"Loaded DEM shape: {dem.shape}")
        print(f"Loaded DEM transform: {dem.transform}")

        # Ensure station coordinates are within DEM bounds
        dem_bounds = dem.bounds
        for coord in sta:
            if not (dem_bounds.left <= coord[0] <= dem_bounds.right and dem_bounds.bottom <= coord[1] <= dem_bounds.top):
                raise ValueError(f"Station coordinate {coord} is outside DEM extent!")

        # Plot DEM and stations
        fig, ax = plt.subplots(figsize=(10, 10))
        dem_data = dem.read(1)
        im = ax.imshow(dem_data, extent=(dem_bounds.left, dem_bounds.right, dem_bounds.bottom, dem_bounds.top), origin='lower', cmap='terrain')
        for i, (x, y) in enumerate(sta):
            ax.plot(x, y, 'ro')
            ax.text(x, y, sta_ids[i], color='white', fontsize=12, ha='right', va='bottom')
        plt.colorbar(im, label='Elevation')
        ax.set_title('DEM with Station Locations')
        ax.set_xlabel('X coordinate')
        ax.set_ylabel('Y coordinate')
        plt.show()

        print(f"Main code - DEM bounds: {dem.bounds}")
        print(f"Main code - Station coordinates:\n{sta}")

        # Calculate spatial distance maps and inter-station distances
        result = spatial_distance.spatial_distance(sta, dem_filepath, verbose=True)

        # Plot the distance matrix
        fig, ax = plt.subplots(figsize=(10, 8))
        im = ax.imshow(result['matrix'], cmap='viridis')
        plt.colorbar(im, label='Distance')
        ax.set_title('Distance Matrix between Stations')
        ax.set_xlabel('Station Index')
        ax.set_ylabel('Station Index')
        for i in range(len(sta)):
            for j in range(len(sta)):
                ax.text(j, i, f"{result['matrix'][i, j]:.2f}", 
                         ha='center', va='center', color='white')
        plt.tight_layout()
        plt.show()

        # Plot the distance maps
        fig, axs = plt.subplots(1, len(sta), figsize=(5*len(sta), 5))
        if len(sta) == 1:
            axs = [axs]
        for i, map_data in enumerate(result['maps']):
            if map_data is not None:
                im = axs[i].imshow(map_data['values'], cmap='viridis', extent=(dem_bounds.left, dem_bounds.right, dem_bounds.bottom, dem_bounds.top), origin='lower')
                axs[i].set_title(f'Distance Map for Station {sta_ids[i]}')
                plt.colorbar(im, ax=axs[i], label='Distance')
                axs[i].plot(sta[i, 0], sta[i, 1], 'ro', markersize=10)
                axs[i].text(sta[i, 0], sta[i, 1], sta_ids[i], color='white', fontsize=12, ha='right', va='bottom')
        plt.tight_layout()
        plt.show()

         # Create synthetic signal
        x = np.arange(1, 1001)
        s = np.vstack([
            norm.pdf(x, 500, 50) * 100,
            norm.pdf(x, 500, 50) * 2,
            norm.pdf(x, 500, 50) * 1
        ])

        # Locate signal using spatial_amplitude
        coupling = np.ones(len(sta))  # Assuming uniform coupling efficiency
        # Locate signal using spatial_amplitude
        e = spatial_amplitude.spatial_amplitude(
            data=s,
            coupling=coupling,
            d_map=result['maps'],  # Pass the distance map dictionaries directly
            v=500,
            q=50,
            f=10
        )

        # Get most likely location coordinates
        e_max = spatial_pmax.spatial_pmax(e)

        # Plot output
        fig, ax = plt.subplots(figsize=(10, 10))
        
        # The result is now a MemoryFile, which can be used like a regular rasterio dataset
        with e.open() as dataset:
            e_data = dataset.read(1)
            im = ax.imshow(e_data, extent=(dem.bounds.left, dem.bounds.right, dem.bounds.bottom, dem.bounds.top), 
                        origin='lower', cmap='viridis')
            plt.colorbar(im, label='Amplitude')
            ax.plot(e_max[0], e_max[1], 'ro', markersize=10, label='Max Amplitude')
            for i, (x, y) in enumerate(sta):
                ax.plot(x, y, 'bo', markersize=8)
                ax.text(x, y, sta_ids[i], color='white', fontsize=12, ha='right', va='bottom')
            ax.set_title('Spatial Amplitude and Most Likely Location')
            ax.set_xlabel('X coordinate')
            ax.set_ylabel('Y coordinate')
            ax.legend()
            plt.show()

    # Clean up
    os.remove(dem_filepath)