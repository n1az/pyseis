import numpy as np
from utils import (
    create_dem,
    convert_to_memoryfile,
    create_signal
)
from plot_utils import (
    plot_dem_with_stations,
    plot_distance_matrix,
    plot_distance_maps,
    plot_amplitude_and_location,
    plot_migrated_and_clipped
)
from data_processing import (
    convert_station_coordinates,
    calculate_spatial_distance,
    locate_signal_amplitude,
    find_maximum_amplitude_location
)
from file_io import save_csv

# Define parameters
xmin, xmax, ymin, ymax = 0, 100, 0, 100
res = (1, 1)
dem_filepath = "dem.tif"
stations = np.array([[25, 25], [75, 75], [50, 90]])
station_ids = ["STA1", "STA2", "STA3"]
input_projection = "+proj=latlong"
output_projection = "+proj=utm +zone=33 +datum=WGS84"
data = create_signal()
coupling = None  # Add appropriate coupling if needed
v = 1.0
q = 1.0
f = 10.0
percentile = 75

# Create DEM
create_dem(xmin, xmax, ymin, ymax, res, dem_filepath)

# Convert station coordinates
converted_stations = convert_station_coordinates(
    stations,
    input_projection,
    output_projection
    )

# Calculate spatial distance
distance_results = calculate_spatial_distance(converted_stations, dem_filepath)

# Convert distance maps to memory files
distance_maps = [convert_to_memoryfile(map_data)
                 for map_data in distance_results["maps"]]

# Locate signal amplitude
amplitude_result = locate_signal_amplitude(
    data=data,
    coupling=coupling,
    d_map=distance_maps,
    v=v,
    q=q,
    f=f
    )

# Find maximum amplitude location
max_amplitude_locations = find_maximum_amplitude_location(
    amplitude_result["e"],
    percentile=percentile
    )

# Save results
plot_dem_with_stations(
    distance_maps[0],
    dem_filepath,
    converted_stations,
    station_ids,
    "dem_with_stations.png"
    )
plot_distance_matrix(
    distance_results["matrix"],
    station_ids,
    "distance_matrix.png"
    )
plot_distance_maps(
    distance_results,
    converted_stations,
    station_ids,
    dem_filepath,
    "distance_maps.png"
    )
plot_amplitude_and_location(
    amplitude_result["e"],
    dem_filepath,
    converted_stations,
    station_ids,
    max_amplitude_locations,
    "amplitude_and_location.png"
    )
plot_migrated_and_clipped(
    amplitude_result["migrated"],
    amplitude_result["clipped"],
    dem_filepath,
    converted_stations,
    station_ids,
    "migrated_result.png",
    "clipped_result.png"
    )
save_csv(
    amplitude_result["matrix"],
    "amplitude_matrix.csv",
    headers=station_ids)
