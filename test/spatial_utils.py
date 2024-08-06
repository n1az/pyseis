from rasterio.io import MemoryFile


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
