import numpy as np
import rasterio
from rasterio.transform import from_origin
import geopandas as gpd
from shapely.geometry import Point, box
import os
import matplotlib.pyplot as plt

def spatial_distance(stations, dem, topography=True, maps=True, matrix=True, aoi=None, verbose=False):
    # PART 0 - check input data ------------------------------------------------
    # open DEM file
    with rasterio.open(dem) as src:
        # check if DEM contains NA values
        if np.any(src.read(1) != src.read(1)):
            raise ValueError("DEM contains NA values!")
        
        # extract coordinates from DEM
        xy_dem = np.array(list(zip(*np.meshgrid(range(src.width), range(src.height)))))
        
        # check if station coordinates are within DEM extent
        if np.any(stations[:,0].min() < src.bounds.left or
                 stations[:,0].max() > src.bounds.right or
                 stations[:,1].min() < src.bounds.bottom or
                 stations[:,1].max() > src.bounds.top):
            raise ValueError("Some station coordinates are outside DEM extent!")
        
        # check/set aoi extent
        if aoi is None:
            aoi_ext = [src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top]
        else:
            aoi_ext = aoi
        
        # check that aoi is within DEM extent
        if np.any(aoi_ext[0] < src.bounds.left or
                 aoi_ext[1] > src.bounds.right or
                 aoi_ext[2] < src.bounds.bottom or
                 aoi_ext[3] > src.bounds.top):
            raise ValueError("AOI extent is beyond DEM extent!")

        # PART 1 - calculate distance maps -----------------------------------------
        if maps:
            # define aoi raster and set values to zero
            aoi_rst = np.zeros((src.height, src.width))
            
            # extract aoi coordinates
            aoi_xy = np.array(list(zip(np.arange(src.height)[::-1], np.arange(src.width))))
            
            # adjust values due to aoi extent
            aoi_rst[(aoi_xy[:,0] >= aoi_ext[2]) &
                    (aoi_xy[:,0] <= aoi_ext[3]) &
                    (aoi_xy[:,1] >= aoi_ext[0]) &
                    (aoi_xy[:,1] <= aoi_ext[1])] = 1
            
            # Create a list to store map data
            maps_data = []
            
            # process each station
            for i in range(stations.shape[0]):
                # optionally print info
                if verbose:
                    print(f"Processing map for station {i}")
                
                # get station coordinates
                xy_stat = stations[i,:]
                
                # get distance map entries
                d = np.zeros(src.height * src.width)
                idx = 0
                for j in range(src.height * src.width):
                    # check if pixel is within aoi
                    if aoi_rst.flat[j] == 1:
                        # get line length
                        l_line = np.sqrt((xy_stat[0] - aoi_xy[j//src.width,0])**2 +
                                         (xy_stat[1] - aoi_xy[j//src.width,1])**2)
                        
                        # get number of points to interpolate along
                        n_int = np.round(l_line / np.mean(src.res)).astype(int)
                        
                        # account for zero (pixel at station)
                        if n_int == 0:
                            n_int = 1
                        
                        # create points along line
                        xy_pts = np.array(list(zip(np.linspace(xy_stat[0], aoi_xy[j//src.width,0], n_int),
                                                 np.linspace(xy_stat[1], aoi_xy[j//src.width,1], n_int))))
                        
                        # create straight line from station to pixel
                        xy_line = gpd.GeoDataFrame({'geometry': [Point(xy) for xy in xy_pts]})
                        
                        # extract elevation data along line
                        z_int = np.array([src.read(1)[int(p.y), int(p.x)] for p in xy_line['geometry']])
                        
                        # interpolate straight line elevation
                        z_dir = np.linspace(z_int[0], z_int[-1], n_int)
                        
                        # optionally calculate along elevation path
                        if topography:
                            i_dir = z_dir > z_int
                            z_dir[i_dir] = z_int[i_dir]
                        
                        # calculate path length
                        l = np.sum(np.sqrt(np.sum((xy_pts[1:] - xy_pts[:-1])**2, axis=1) +
                                    (z_dir[1:] - z_dir[:-1])**2))
                    else:
                        l = np.nan
                    
                    # store distance map entry
                    d[j] = l
                    idx += 1
                
                # Store the map data in memory
                maps_data.append({
                    'crs': src.crs,
                    'transform': src.transform,
                    'shape': src.shape,
                    'values': d.reshape(src.shape)
                })
        else:
            maps_data = [None] * stations.shape[0]
        
        # create output station distance matrix
        M = np.zeros((stations.shape[0], stations.shape[0]))
        
        if matrix:
            # optionally, print info
            if verbose:
                print("Processing station distances")
            
            # create straight line from station to pixel
            xy_stat = gpd.GeoDataFrame({'geometry': [Point(xy) for xy in stations]}, crs=src.crs)
            
            # Create a GeoDataFrame from the DEM extent
            dem_bounds = box(src.bounds.left, src.bounds.bottom, src.bounds.right, src.bounds.top)
            dem_gdf = gpd.GeoDataFrame({'geometry': [dem_bounds]}, crs=src.crs)
            
            # extract elevation data for stations
            xyz_stat = gpd.sjoin(xy_stat, dem_gdf, how='left', predicate='within')
            xyz_stat['z'] = [src.read(1)[src.index(point.x, point.y)] for point in xyz_stat['geometry']]
            
            # loop through all stations
            for i in range(stations.shape[0]):
                # loop through all stations
                for j in range(stations.shape[0]):
                    # get number of points to interpolate along
                    l_line = np.sqrt((stations[i,0] - stations[j,0])**2 + (stations[i,1] - stations[j,1])**2)
                    n_int = max(int(np.round(l_line / np.mean(src.res))), 2)
                    
                    # create points along line
                    xy_pts = np.array(list(zip(np.linspace(stations[i,0], stations[j,0], n_int),
                                               np.linspace(stations[i,1], stations[j,1], n_int))))
                    
                    # extract elevation data along line
                    z_int = np.array([src.read(1)[src.index(x, y)] for x, y in xy_pts])
                    
                    # interpolate straight line elevation
                    z_dir = np.linspace(z_int[0], z_int[-1], n_int)
                    
                    # optionally calculate along elevation path
                    if topography:
                        i_dir = z_dir > z_int
                        z_dir[i_dir] = z_int[i_dir]
                    
                    # calculate path length and assign it to output data set
                    seg_lengths = np.sqrt(np.sum((xy_pts[1:] - xy_pts[:-1])**2, axis=1) + 
                                          (z_dir[1:] - z_dir[:-1])**2)
                    M[i,j] = np.sum(seg_lengths)
    
    # return output
    return {'maps': maps_data, 'matrix': M}


# Example
if __name__ == "__main__":
    
    # Example code to run the function
    stations = np.array([[25, 25], [75, 75], [50, 50]])  # Example station coordinates

    # Create a temporary DEM file
    dem_data = np.random.rand(100, 100) * 1000  # 100x100 DEM with random elevation data
    dem_path = 'temporary_dem.tif'
    with rasterio.open(
        dem_path, 'w',
        driver='GTiff',
        height=dem_data.shape[0],
        width=dem_data.shape[1],
        count=1,
        dtype=dem_data.dtype,
        crs='+proj=latlong',
        transform=from_origin(0, 100, 1, 1)) as dst:
        dst.write(dem_data, 1)

    # Run the spatial_distance function
    result = spatial_distance(stations, dem_path, verbose=True)

    # Plot the distance matrix
    plt.figure(figsize=(10, 8))
    plt.imshow(result['matrix'], cmap='viridis')
    plt.colorbar(label='Distance')
    plt.title('Distance Matrix between Stations')
    plt.xlabel('Station Index')
    plt.ylabel('Station Index')
    for i in range(len(stations)):
        for j in range(len(stations)):
            plt.text(j, i, f"{result['matrix'][i, j]:.2f}", 
                     ha='center', va='center', color='white')
    plt.tight_layout()
    plt.show()

    # Plot the distance maps
    fig, axs = plt.subplots(1, len(stations), figsize=(5*len(stations), 5))
    if len(stations) == 1:
        axs = [axs]
    for i, map_data in enumerate(result['maps']):
        if map_data is not None:
            im = axs[i].imshow(map_data['values'], cmap='viridis')
            axs[i].set_title(f'Distance Map for Station {i}')
            plt.colorbar(im, ax=axs[i], label='Distance')
    plt.tight_layout()
    plt.show()

    # Delete the temporary DEM file
    os.remove(dem_path)