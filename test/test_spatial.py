import numpy as np
import rasterio
from scipy.stats import norm
import os

from pyseis import (
    spatial_distance,
    spatial_migrate,
    spatial_clip,
    spatial_convert,
    spatial_amplitude,
    spatial_pmax,
)
from utils import save_csv
from dem_utils import create_dem
from spatial_utils import convert_to_memoryfile
from plot_utils import (
    plot_dem_with_stations,
    plot_distance_matrix,
    plot_distance_maps,
    plot_spatial_amplitude,
    plot_migration_results,
)


def main():
    """
    Main function to perform spatial analysis on synthetic data.

    This function creates a synthetic DEM, calculates spatial distances,
    performs spatial amplitude analysis, and applies spatial migration.
    It also saves relevant plots and data to CSV files.
    """
    # Define station coordinates (in the same coordinate system as the DEM)
    sta = np.array([[25, 25], [75, 75], [50, 90]])
    sta_ids = ["A", "B", "C"]

    # Define the input and output projection systems
    input_proj = "+proj=longlat +datum=WGS84"
    output_proj = "+proj=utm +zone=32 +datum=WGS84"

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
        0,
        100,
        0,
        100,
        res=(1, 1),
        filepath="synthetic_dem_0.tif"
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
                if not (dem_bounds.left <= coord[0] <= dem_bounds.right
                        and dem_bounds.bottom <= coord[1] <= dem_bounds.top):
                    raise ValueError(
                        f"Station coordinate {coord} is outside DEM extent!"
                        )

            # Plot DEM and stations
            plot_dem_with_stations(dem, sta, sta_ids)

            print(f"Main code - DEM bounds: {dem.bounds}")
            print(f"Main code - Station coordinates:\n{sta}")

            # Calculate spatial distance maps and inter-station distances
            result = spatial_distance.spatial_distance(
                sta,
                dem_filepath,
                verbose=True
                )

        # Plot the distance matrix
        plot_distance_matrix(result, sta_ids)

        # Save distance matrix to CSV
        save_csv(result["matrix"], "distance_matrix.csv", headers=sta_ids)

        # Plot the distance maps
        plot_distance_maps(result, dem_bounds, sta, sta_ids)

        # Create synthetic signal
        x = np.arange(1, 1001)
        s = np.vstack(
            [norm.pdf(x, 500, 50) * 100,
             norm.pdf(x, 500, 50) * 2, norm.pdf(x, 500, 50) * 1])

        # Save synthetic signal to CSV
        save_csv(s.T, "Py_spatial_synth_signal.csv", headers=sta_ids)

        # Locate signal using spatial_amplitude
        coupling = np.ones(len(sta))  # Assuming uniform coupling efficiency
        e = spatial_amplitude.spatial_amplitude(
            data=s,
            coupling=coupling,
            d_map=result["maps"],
            v=500,
            q=50,
            f=10)

        # Get most likely location coordinates
        e_max_list = spatial_pmax.spatial_pmax(e)
        print("e_max_list:", e_max_list)
        save_csv(e_max_list, "Py_pmax.csv")

        # Plot output
        plot_spatial_amplitude(e, dem_bounds, e_max_list, sta, sta_ids)

        # Create synthetic seismic signals
        num_samples = 1000
        t = np.linspace(0, 10, num_samples)
        data = []
        for i in range(len(sta)):
            # Different amplitudes for each station
            signal = norm.pdf(t, 5, 0.5) * (i + 1) * 100
            noise = np.random.normal(0, 0.1, num_samples)
            data.append(signal + noise)
        data = np.array(data)

        # Save synthetic seismic signals to CSV
        save_csv(data.T, "Py_synth_seis_signals.csv", headers=sta_ids)

        # Set parameters for spatial_migrate
        v = 3000.0  # Velocity in m/s (as float)
        dt = t[1] - t[0]  # Time step

        # Convert distance maps to MemoryFile objects and open them
        memory_files = [convert_to_memoryfile(map_data)
                        for map_data in result["maps"]]

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
            migrated_result,
            quantile=0.75,
            replace=np.nan,
            normalise=True
            )

        # Plot the migrated and clipped results
        migrated_data, clipped_data = plot_migration_results(
            migrated_result,
            clipped_result,
            dem_bounds,
            sta,
            sta_ids
            )

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


if __name__ == "__main__":
    main()
    print("Script completed.")
