import argparse
import numpy as np
import rasterio
from rasterio.io import MemoryFile
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
from utils.file_utils import save_csv
from utils.dem_utils import create_dem
from utils.plot_utils import (
    plot_dem_with_stations,
    plot_distance_matrix,
    plot_distance_maps,
    plot_spatial_amplitude,
    plot_migration_results,
)


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
    return memfile.open()


def setup_stations():
    """
    Set up station coordinates and convert them.

    Returns:
        tuple: A tuple containing the station coordinates array and
               station IDs list.
    """
    sta = np.array([[25, 25], [75, 75], [50, 90]])
    sta_ids = ["A", "B", "C"]
    input_proj = "+proj=longlat +datum=WGS84"
    output_proj = "+proj=utm +zone=32 +datum=WGS84"
    converted_sta = spatial_convert.spatial_convert(
        sta, input_proj, output_proj)

    print("Original station coordinates:")
    print(sta)
    save_csv(sta, "Py_original_stations.csv")
    print("\nConverted station coordinates:")
    print(converted_sta)
    save_csv(converted_sta, "Py_converted_stations.csv")

    return sta, sta_ids


def create_synthetic_dem():
    """
    Create a synthetic Digital Elevation Model (DEM).

    Returns:
        str: Filepath of the created synthetic DEM.
    """
    return create_dem(
        0, 100, 0, 100, res=(1, 1), filepath="synthetic_dem_0.tif")


def create_synthetic_signal(num_stations):
    """
    Create a synthetic signal for the given number of stations.

    Args:
        num_stations (int): Number of stations.

    Returns:
        numpy.ndarray: 2D array of synthetic signals.
    """
    x = np.arange(1, 1001)
    s = np.vstack([norm.pdf(x, 500, 50) * 100 / (i + 1)
                   for i in range(num_stations)])
    save_csv(s.T, "Py_spatial_synth_signal.csv",
             headers=[f"Station_{i}" for i in range(num_stations)])
    return s


def create_synthetic_seismic_signals(num_samples, num_stations):
    """
    Create synthetic seismic signals for the given parameters.

    Args:
        num_samples (int): Number of samples in each signal.
        num_stations (int): Number of stations.

    Returns:
        tuple: A tuple containing the synthetic data array and time array.
    """
    t = np.linspace(0, 10, num_samples)
    data = []
    for i in range(num_stations):
        signal = norm.pdf(t, 5, 0.5) * (i + 1) * 100
        noise = np.random.normal(0, 0.1, num_samples)
        data.append(signal + noise)
    data = np.array(data)
    save_csv(data.T, "Py_synth_seis_signals.csv",
             headers=[f"Station_{i}" for i in range(num_stations)])
    return data, t


def parse_arguments():
    """
    Parse command line arguments.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description='Create synthetic seismic signals')
    parser.add_argument(
        '--n', type=int, default=1000, help='Number of samples')
    parser.add_argument(
        '--v', type=float, default=3000.0, help='Velocity in m/s (float)')
    return parser.parse_args()


def perform_spatial_distance(dem, sta, sta_ids):
    """
    Perform spatial distance calculations and plotting.

    Args:
        dem (rasterio.io.DatasetReader): Opened DEM dataset.
        sta (numpy.ndarray): Station coordinates.
        sta_ids (list): Station IDs.

    Returns:
        dict: Result of spatial distance calculations.
    """
    result = spatial_distance.spatial_distance(sta, dem.name, verbose=True)
    plot_distance_matrix(result, sta_ids)
    save_csv(result["matrix"], "distance_matrix.csv", headers=sta_ids)
    plot_distance_maps(result, dem.bounds, sta, sta_ids)
    return result


def perform_spatial_amplitude(s, dem, coupling, result, sta, sta_ids):
    """
    Perform spatial amplitude calculations and plotting.

    Args:
        s (numpy.ndarray): Synthetic signal data.
        dem (rasterio.io.DatasetReader): Opened DEM dataset.
        coupling (numpy.ndarray): Coupling efficiency array.
        result (dict): Result from spatial distance calculations.
        sta (numpy.ndarray): Station coordinates.
        sta_ids (list): Station IDs.

    Returns:
        tuple: A tuple containing the amplitude result and max list.
    """
    e = spatial_amplitude.spatial_amplitude(data=s, coupling=coupling,
                                            d_map=result["maps"], v=500,
                                            q=50, f=10)
    e_max_list = spatial_pmax.spatial_pmax(e)
    print("e_max_list:", e_max_list)
    save_csv(e_max_list, "Py_pmax.csv")
    plot_spatial_amplitude(e, dem.bounds, e_max_list, sta, sta_ids)
    return e, e_max_list


def perform_spatial_migration(data, sta, sta_ids, dem, result, v, dt,
                              memory_files):
    """
    Perform spatial migration calculations and plotting.

    Args:
        data (numpy.ndarray): Synthetic seismic signal data.
        sta (numpy.ndarray): Station coordinates.
        sta_ids (list): Station IDs.
        dem (rasterio.io.DatasetReader): Opened DEM dataset.
        result (dict): Result from spatial distance calculations.
        v (float): Velocity.
        dt (float): Time step.
        memory_files (list): List of opened MemoryFile objects.

    Returns:
        tuple: A tuple containing migrated result, clipped result,
               migrated data, and clipped data.
    """
    migrated_result = spatial_migrate.spatial_migrate(
        data=data,
        d_stations=result["matrix"],
        d_map=memory_files,
        v=v,
        dt=dt,
        verbose=True,
    )
    clipped_result = spatial_clip.spatial_clip(migrated_result, quantile=0.75,
                                               replace=np.nan, normalise=True)
    migrated_data, clipped_data = plot_migration_results(
        migrated_result, clipped_result, dem.bounds, sta, sta_ids
    )
    save_csv(migrated_data, "Py_spatial_migrated_data.csv")
    save_csv(clipped_data, "Py_spatial_clipped_data.csv")
    return migrated_result, clipped_result, migrated_data, clipped_data


def print_summary_statistics(clipped_data, migrated_data):
    """
    Print summary statistics for clipped and migrated data.

    Args:
        clipped_data (numpy.ndarray): Clipped data array.
        migrated_data (numpy.ndarray): Migrated data array.
    """
    print("\nClipped migrated data summary:")
    print(f"Min value: {np.nanmin(clipped_data)}")
    print(f"Max value: {np.nanmax(clipped_data)}")
    print(f"Mean value: {np.nanmean(clipped_data)}")
    print("\nMigrated data summary:")
    print(f"Min value: {np.min(migrated_data)}")
    print(f"Max value: {np.max(migrated_data)}")
    print(f"Mean value: {np.mean(migrated_data)}")


def main():
    """
    Main function to run the spatial analysis pipeline.
    """
    args = parse_arguments()
    sta, sta_ids = setup_stations()
    dem_filepath = create_synthetic_dem()

    memory_files = []

    try:
        with rasterio.open(dem_filepath) as dem:
            print(f"Loaded DEM bounds: {dem.bounds}")
            print(f"Loaded DEM shape: {dem.shape}")
            print(f"Loaded DEM transform: {dem.transform}")

            for coord in sta:
                if not (dem.bounds.left <= coord[0] <= dem.bounds.right and
                        dem.bounds.bottom <= coord[1] <= dem.bounds.top):
                    raise ValueError(
                        f"Station coordinate {coord} is outside DEM extent!"
                    )

            plot_dem_with_stations(dem, sta, sta_ids)

            print(f"Main code - DEM bounds: {dem.bounds}")
            print(f"Main code - Station coordinates:\n{sta}")

            result = perform_spatial_distance(dem, sta, sta_ids)

            s = create_synthetic_signal(len(sta))
            coupling = np.ones(len(sta))
            e, e_max_list = perform_spatial_amplitude(s, dem, coupling, result,
                                                      sta, sta_ids)

            data, t = create_synthetic_seismic_signals(args.n, len(sta))
            dt = t[1] - t[0]

            memory_files = [convert_to_memoryfile(map_data)
                            for map_data in result["maps"]]
            migrated_result, clipped_result, migrated_data, clipped_data = \
                perform_spatial_migration(data, sta, sta_ids, dem, result,
                                          args.v, dt, memory_files)

            print_summary_statistics(clipped_data, migrated_data)

    except Exception as e:
        print(f"An error occurred: {str(e)}")

    finally:
        for memfile in memory_files:
            memfile.close()
        if 'migrated_result' in locals():
            migrated_result.close()
        if 'clipped_result' in locals():
            clipped_result.close()

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
