import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm
import rasterio
from rasterio.transform import from_origin
from rasterio.io import MemoryFile
import os


from pyseis import (
    spatial_distance,
    spatial_migrate,
    spatial_clip,
    spatial_convert,
    spatial_amplitude,
    spatial_pmax,
)
from test_fmi_models import save_plot, save_csv


# Function to create a synthetic DEM and save it to a file
def create_dem(xmin, xmax, ymin, ymax, res, filepath):
    """
    Create a synthetic Digital Elevation Model (DEM) and save it to a file.

    Args:
        xmin (float): Minimum x-coordinate of the DEM.
        xmax (float): Maximum x-coordinate of the DEM.
        ymin (float): Minimum y-coordinate of the DEM.
        ymax (float): Maximum y-coordinate of the DEM.
        res (tuple): Resolution of the DEM in (x, y) direction.
        filepath (str): Path to save the DEM file.

    Returns:
        str: Path to the saved DEM file.
    """
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
    dem = (np.sin(5 * X) * np.cos(5 * Y) + np.random.rand(
        height,
        width) * 0.1) * 100

    with rasterio.open(
        filepath,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=1,
        dtype=dem.dtype,
        crs="+proj=latlong",
        transform=transform,
    ) as dst:
        dst.write(dem, 1)

    print(f"DEM created and saved to {filepath}")
    return filepath


def convert_to_memoryfile(map_data):
    """
    Convert a distance map dictionary to a MemoryFile object.

    Args:
        map_data (dict): Dictionary containing the distance map data.

    Returns:
        rasterio.io.MemoryFile: Opened MemoryFile dataset.
    """
    profile = {
        "driver": "GTiff",
        "height": map_data["values"].shape[0],
        "width": map_data["values"].shape[1],
        "count": 1,
        "dtype": map_data["values"].dtype,
        "crs": map_data["crs"],
        "transform": map_data["transform"],
    }
    memfile = MemoryFile()
    with memfile.open(**profile) as dataset:
        dataset.write(map_data["values"], 1)
    return memfile.open()  # Return the opened dataset


# Main code
if __name__ == "__main__":
    """
    Main function to perform spatial analysis on synthetic data.

    This function creates a synthetic DEM, calculates spatial distances,
    performs spatial amplitude analysis, and applies spatial migration.
    It also saves relevant plots and data to CSV files.
    """
    # Define station coordinates (in the same coordinate system as the DEM)
    # Adjusted to be within DEM bounds
    sta = np.array([[25, 25], [75, 75], [50, 90]])
    sta_ids = ["A", "B", "C"]

    # Define the input and output projection systems
    # Example: WGS84 geographic coordinates
    input_proj = "+proj=longlat +datum=WGS84"
    output_proj = "+proj=utm +zone=32 +datum=WGS84"  # Example: UTM zone 32N

    # Convert station coordinates
    converted_sta = spatial_convert.spatial_convert(
        sta,
        input_proj,
        output_proj
    )

    print("Original station coordinates:")
    print(sta)
    save_csv(sta, "Py_original_stations.csv")
    print("\nConverted station coordinates:")
    print(converted_sta)
    save_csv(converted_sta, "Py_converted_stations.csv")

    # Create and save synthetic DEM
    dem_filepath = create_dem(
        0, 100, 0, 100, res=(1, 1), filepath="synthetic_dem_0.tif"
    )

    dem = None
    result = None
    memory_files = []
    migrated_result = None

    try:
        # Read the DEM back in as a rasterio object
        with rasterio.open(dem_filepath) as dem:
            print(f"Loaded DEM bounds: {dem.bounds}")
            print(f"Loaded DEM shape: {dem.shape}")
            print(f"Loaded DEM transform: {dem.transform}")

            # Ensure station coordinates are within DEM bounds
            dem_bounds = dem.bounds
            for coord in sta:
                if not (
                    dem_bounds.left <= coord[0] <= dem_bounds.right
                    and dem_bounds.bottom <= coord[1] <= dem_bounds.top
                ):
                    raise ValueError(
                        f"Station coordinate {coord} is outside DEM extent!"
                    )

            # Plot DEM and stations
            fig, ax = plt.subplots(figsize=(10, 10))
            dem_data = dem.read(1)
            im = ax.imshow(
                dem_data,
                extent=(
                    dem_bounds.left,
                    dem_bounds.right,
                    dem_bounds.bottom,
                    dem_bounds.top,
                ),
                origin="lower",
                cmap="terrain",
            )
            for i, (x, y) in enumerate(sta):
                ax.plot(x, y, "ro")
                ax.text(
                    x,
                    y,
                    sta_ids[i],
                    color="white",
                    fontsize=12,
                    ha="right",
                    va="bottom",
                )
            plt.colorbar(im, label="Elevation")
            ax.set_title("DEM with Station Locations")
            ax.set_xlabel("X coordinate")
            ax.set_ylabel("Y coordinate")
            save_plot(fig, "Py_spatial_dist_0.png")
            plt.close()

            print(f"Main code - DEM bounds: {dem.bounds}")
            print(f"Main code - Station coordinates:\n{sta}")

            # Calculate spatial distance maps and inter-station distances
            result = spatial_distance.spatial_distance(
                sta,
                dem_filepath,
                verbose=True
            )

        # Plot the distance matrix
        fig, ax = plt.subplots(figsize=(10, 8))
        im = ax.imshow(result["matrix"], cmap="viridis")
        plt.colorbar(im, label="Distance")
        ax.set_title("Distance Matrix between Stations")
        ax.set_xlabel("Station Index")
        ax.set_ylabel("Station Index")
        for i in range(len(sta)):
            for j in range(len(sta)):
                ax.text(
                    j,
                    i,
                    f"{result['matrix'][i, j]:.2f}",
                    ha="center",
                    va="center",
                    color="white",
                )
        plt.tight_layout()
        save_plot(fig, "Py_spatial_dist_mat.png")
        plt.close()

        # Save distance matrix to CSV
        save_csv(result["matrix"], "distance_matrix.csv", headers=sta_ids)

        # Plot the distance maps
        fig, axs = plt.subplots(1, len(sta), figsize=(5 * len(sta), 5))
        if len(sta) == 1:
            axs = [axs]
        for i, map_data in enumerate(result["maps"]):
            if map_data is not None:
                im = axs[i].imshow(
                    map_data["values"],
                    cmap="viridis",
                    extent=(
                        dem_bounds.left,
                        dem_bounds.right,
                        dem_bounds.bottom,
                        dem_bounds.top,
                    ),
                    origin="lower",
                )
                axs[i].set_title(f"Distance Map for Station {sta_ids[i]}")
                plt.colorbar(im, ax=axs[i], label="Distance")
                axs[i].plot(sta[i, 0], sta[i, 1], "ro", markersize=10)
                axs[i].text(
                    sta[i, 0],
                    sta[i, 1],
                    sta_ids[i],
                    color="white",
                    fontsize=12,
                    ha="right",
                    va="bottom",
                )
        plt.tight_layout()
        save_plot(fig, "distance_maps.png")
        plt.close()

        # Create synthetic signal
        x = np.arange(1, 1001)
        s = np.vstack(
            [
                norm.pdf(x, 500, 50) * 100,
                norm.pdf(x, 500, 50) * 2,
                norm.pdf(x, 500, 50) * 1,
            ]
        )

        # Save synthetic signal to CSV
        save_csv(s.T, "Py_spatial_synth_signal.csv", headers=sta_ids)

        # Locate signal using spatial_amplitude
        coupling = np.ones(len(sta))  # Assuming uniform coupling efficiency
        # Locate signal using spatial_amplitude
        e = spatial_amplitude.spatial_amplitude(
            data=s,
            coupling=coupling,
            d_map=result["maps"],
            v=500,
            q=50,
            f=10,
        )

        # Get most likely location coordinates
        e_max_list = spatial_pmax.spatial_pmax(e)
        print("e_max_list:", e_max_list)
        save_csv(e_max_list, "Py_pmax.csv")

        # Plot output
        fig, ax = plt.subplots(figsize=(10, 10))

        # The result is now a MemoryFile(regular rasterio dataset)
        with e.open() as dataset:
            e_data = dataset.read(1)
            im = ax.imshow(
                e_data,
                extent=(
                    dem.bounds.left,
                    dem.bounds.right,
                    dem.bounds.bottom,
                    dem.bounds.top,
                ),
                origin="lower",
                cmap="viridis",
            )
            plt.colorbar(im, label="Amplitude")

            # Plot all maximum amplitude locations
            if e_max_list:
                for i, e_max in enumerate(e_max_list):
                    ax.plot(
                        e_max[0],
                        e_max[1],
                        "ro",
                        markersize=10,
                        label=f"Max Amplitude {i+1}" if i == 0 else "",
                    )
                for i, (x, y) in enumerate(sta):
                    ax.plot(x, y, "bo", markersize=8)
                    ax.text(
                        x,
                        y,
                        sta_ids[i],
                        color="white",
                        fontsize=12,
                        ha="right",
                        va="bottom",
                    )
                ax.set_title("Spatial Amplitude and Most Likely Location(s)")
                ax.set_xlabel("X coordinate")
                ax.set_ylabel("Y coordinate")
                ax.legend()
                save_plot(fig, "Py_spatial_amp.png")
                plt.close()
            else:
                print("No maximum amplitude points found.")

        # Create synthetic seismic signals
        num_samples = 1000
        t = np.linspace(0, 10, num_samples)
        data = []
        for i in range(len(sta)):
            signal = (
                norm.pdf(t, 5, 0.5) * (i + 1) * 100
            )  # Different amplitudes for each station
            noise = np.random.normal(0, 0.1, num_samples)
            data.append(signal + noise)
        data = np.array(data)

        # Save synthetic seismic signals to CSV
        save_csv(data.T, "Py_synth_seis_signals.csv", headers=sta_ids)

        # Set parameters for spatial_migrate
        v = 3000.0  # Velocity in m/s (as float)
        dt = t[1] - t[0]  # Time step

        # Convert distance maps to MemoryFile objects and open them
        memory_files = [convert_to_memoryfile(
            map_data
        ) for map_data in result["maps"]]

        # Call spatial_migrate function
        migrated_result = spatial_migrate.spatial_migrate(
            data=data,
            d_stations=result["matrix"],
            d_map=memory_files,  # Pass the opened MemoryFile objects
            v=v,
            dt=dt,
            verbose=True,
        )

        # Apply spatial clipping to the migrated result
        clipped_result = spatial_clip.spatial_clip(
            migrated_result, quantile=0.75, replace=np.nan, normalise=True
        )

        # Plot the clipped migrated result
        fig, ax = plt.subplots(figsize=(10, 10))

        # Original migrated result
        migrated_data = migrated_result.read(1)
        im1 = ax.imshow(
            migrated_data,
            extent=(
                dem_bounds.left,
                dem_bounds.right,
                dem_bounds.bottom,
                dem_bounds.top,
            ),
            origin="lower",
            cmap="viridis",
        )
        plt.colorbar(im1, ax=ax, label="Migration Value")
        ax.set_title("Original Spatial Migration Result")
        ax.set_xlabel("X coordinate")
        ax.set_ylabel("Y coordinate")

        # Plot station locations on original result
        for i, (x, y) in enumerate(sta):
            ax.plot(x, y, "ro", markersize=8)
            ax.text(
                x,
                y,
                sta_ids[i],
                color="white",
                fontsize=12,
                ha="right",
                va="bottom"
            )
        save_plot(fig, "Py_spatial_migration.png")
        plt.close()

        fig, ax = plt.subplots(figsize=(10, 10))
        # Clipped migrated result
        clipped_data = clipped_result.read(1)
        im2 = ax.imshow(
            clipped_data,
            extent=(
                dem_bounds.left,
                dem_bounds.right,
                dem_bounds.bottom,
                dem_bounds.top,
            ),
            origin="lower",
            cmap="viridis",
        )
        plt.colorbar(im2, ax=ax, label="Clipped Migration Value")
        ax.set_title("Clipped Spatial Migration Result (75th percentile)")
        ax.set_xlabel("X coordinate")
        ax.set_ylabel("Y coordinate")

        # Plot station locations on clipped result
        for i, (x, y) in enumerate(sta):
            ax.plot(x, y, "ro", markersize=8)
            ax.text(
                x,
                y,
                sta_ids[i],
                color="white",
                fontsize=12,
                ha="right",
                va="bottom"
            )

        plt.tight_layout()
        save_plot(fig, "Py_spatial_clipped.png")
        plt.close()

        # Save migrated and clipped data to CSV
        save_csv(migrated_data, "Py_spatial_migrated_data.csv")
        save_csv(clipped_data, "Py_spatial_clipped_data.csv")

        # Print summary statistics of the clipped result
        print("\nClipped migrated data summary:")
        print(f"Min value: {np.nanmin(clipped_data)}")
        print(f"Max value: {np.nanmax(clipped_data)}")
        print(f"Mean value: {np.nanmean(clipped_data)}")

        # Print summary statistics of the migrated result
        print("\nMigrated data summary:")
        print(f"Min value: {np.min(migrated_data)}")
        print(f"Max value: {np.max(migrated_data)}")
        print(f"Mean value: {np.mean(migrated_data)}")

    except Exception as e:
        print(f"An error occurred: {str(e)}")

    finally:
        # Clean up
        if dem is not None:
            dem.close()
        if result is not None and "maps" in result:
            for map_data in result["maps"]:
                if isinstance(map_data, rasterio.io.DatasetReader):
                    map_data.close()
        for memfile in memory_files:
            memfile.close()
        if migrated_result is not None:
            migrated_result.close()
        if "clipped_result" in locals() and clipped_result is not None:
            clipped_result.close()

        # Now try to remove the file
        try:
            os.remove(dem_filepath)
            print(f"Successfully removed {dem_filepath}")
        except PermissionError:
            print(f"Could not remove {dem_filepath}. It may still be in use.")
        except Exception as e:
            print(f"An error occurred removing {dem_filepath}: {str(e)}")

print("Script completed.")
