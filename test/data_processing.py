from pyseis import spatial_convert, spatial_distance, spatial_amplitude
from pyseis import spatial_pmax


def convert_station_coordinates(sta, input_proj, output_proj):
    return spatial_convert.spatial_convert(sta, input_proj, output_proj)


def calculate_spatial_distance(sta, dem_filepath):
    return spatial_distance.spatial_distance(sta, dem_filepath, verbose=True)


def locate_signal_amplitude(data, coupling, d_map, v, q, f):
    return spatial_amplitude.spatial_amplitude(
        data=data,
        coupling=coupling,
        d_map=d_map,
        v=v,
        q=q,
        f=f
        )


def find_maximum_amplitude_location(e, percentile):
    return spatial_pmax.spatial_pmax(e, percentile=percentile)
