import argparse
import numpy as np
import rasterio
from rasterio.warp import transform


def spatial_convert(data, from_proj, to_proj):
    """
    Convert coordinates between reference systems.

    Parameters:
    data (numpy.ndarray or list): x-, y-coordinates to be converted.
    from_proj (str): proj4 string of the input reference system.
    to_proj (str): proj4 string of the output reference system.

    Returns:
    numpy.ndarray: Converted coordinates.


    Examples:
    >>> xy = np.array([13, 55])
    >>> proj_in = "+proj=longlat +datum=WGS84"
    >>> proj_out = "+proj=utm +zone=32 +datum=WGS84"
    >>> spatial_convert(xy, proj_in, proj_out)
    array([[397897.06062277, 6098621.31925031]])

    >>> xy = np.array([[10, 54], [11, 55]])
    >>> spatial_convert(xy, proj_in, proj_out)
    array([[328654.54236693, 5989452.12391145],
           [339379.35524679, 6098673.89450301]])
    """
    # Check input data
    if isinstance(data, np.ndarray):
        if data.ndim == 1 and data.shape[0] == 2:
            data = np.array([data])
        elif data.ndim == 2 and data.shape[1] == 2:
            data = data
        else:
            raise ValueError(
                "Coordinate data must contain only 2 values (x and y) \
                    or 2 columns (x and y)!"
            )
    elif isinstance(data, list):
        if len(data) == 2:
            data = np.array([data])
        elif len(data) > 2 and all(len(coord) == 2 for coord in data):
            data = np.array(data)
        else:
            raise ValueError(
                "Coordinate data must contain only 2 values (x and y) \
                    or 2 columns (x and y)!"
            )
    else:
        raise ValueError("Input data must be a numpy.ndarray or a list!")

    # Convert coordinates
    with rasterio.Env():
        xs, ys = data[:, 0], data[:, 1]
        converted_xs, converted_ys = transform(from_proj, to_proj, xs, ys)

    return np.column_stack((converted_xs, converted_ys))


if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description='Spatial Cconvert example.')
    parser.add_argument(
        '--sta-a',
        type=int,
        default=25,
        help='Station coordinate for A')
    parser.add_argument(
        '--sta-b',
        type=int,
        default=75,
        help='Station coordinate for B')
    parser.add_argument(
        '--sta-c',
        type=int,
        default=50,
        help='Station coordinate for C')

    # Parse command line arguments
    args = parser.parse_args()

    # Define station coordinates (in the same coordinate system as the DEM)
    sta = np.array(
        [[args.sta_a, args.sta_a], [args.sta_b, args.sta_b], [args.sta_c, 90]]
        )
    sta_ids = ["A", "B", "C"]

    # Define the input and output projection systems
    input_proj = "+proj=longlat +datum=WGS84"
    output_proj = "+proj=utm +zone=32 +datum=WGS84"

    # Convert station coordinates
    converted_sta = spatial_convert(
        sta,
        input_proj,
        output_proj
        )

    print("Original station coordinates:")
    print(sta)
    print("\nConverted station coordinates:")
    print(converted_sta)
