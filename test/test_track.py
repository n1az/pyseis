import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from scipy.stats import norm
from multiprocessing import Pool, cpu_count
import rasterio
from rasterio.transform import from_origin
from typing import List, Dict, Tuple, Optional, Callable
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os
import sys

# Add the parent directory to the path to import custom functions
script_directory = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(script_directory, '..'))

from bin import spatial_distance

# Define model functions outside of spatial_track
def surf_spread_atten(d, a_0, f, q, v):
    return a_0 / np.sqrt(d) * np.exp(-((np.pi * f * d) / (q * v)))

def body_spread_atten(d, a_0, f, q, v):
    return a_0 / d * np.exp(-((np.pi * f * d) / (q * v)))

def surf_body_spread_atten(d, a_0, f, q, v, k):
    return (k * a_0 / np.sqrt(d) * np.exp(-((np.pi * f * d) / (q * v)))) + \
           ((1 - k) * a_0 / d * np.exp(-((np.pi * f * d) / (q * v))))

def surf_spread(d, a_0):
    return a_0 / np.sqrt(d)

def body_spread(d, a_0):
    return a_0 / d

def surf_body_spread(d, a_0, k):
    return k * a_0 / np.sqrt(d) + (1 - k) * a_0 / d

def spatial_track(
    data: List[Dict],
    d_map: Dict,
    window: float = 5.0,
    overlap: float = 0,
    v: float = 800,
    q: float = 40,
    f: float = 12,
    qt: float = 1,
    model: str = "SurfSpreadAtten",
    coupling: Optional[List[float]] = None,
    aoi: Optional[np.ndarray] = None,
    k: Optional[float] = None,
    dt: Optional[float] = None,
    cpu: Optional[float] = None,
    verbose: bool = False,
    plot: bool = False
) -> Dict:
    """
    Track a spatially mobile seismic source.

    This function allows tracking a spatially mobile seismic source and
    thereby estimating the source amplitude and the model's variance
    reduction as a measure of quality or robustness of the time-resolved
    estimates.

    Args:
        data (List[Dict]): Seismic signals used for source tracking. Each dictionary should contain
                           'signal' and 'meta' keys.
        coupling (Optional[List[float]]): Coupling efficiency factors for each seismic station.
        window (float): Time window for which the source is tracked.
        overlap (float): Fraction of overlap of time windows used for source tracking.
        d_map (Dict): Distance maps for each station. Output of spatial_distance function.
        aoi (Optional[np.ndarray]): Area of interest that defines which pixels are used to locate the source.
        v (float): Mean velocity of seismic waves (m/s).
        q (float): Quality factor of the ground.
        f (float): Frequency for which to model the attenuation.
        k (Optional[float]): Fraction of surface wave contribution to signals.
        qt (float): Quantile threshold that defines acceptable location estimates.
        dt (Optional[float]): Sampling frequency. Only required if input signals are not in the expected format.
        model (str): Amplitude-distance function model to use.
        cpu (Optional[float]): Fraction of CPUs to use for parallel processing.
        verbose (bool): Enable screen output of processing progress.
        plot (bool): Enable graphical output of key results.

    Returns:
        Dict: A dictionary containing summarizing statistics of the fits.

    Note:
        This function is based on ideas published by Burtin et al. (2016),
        Walter et al. (2017) and Perez-Guillen et al. (2019).
    """
    
     # Check/convert input signal structure
    if not isinstance(data[0], dict):
        if dt is None:
            raise ValueError("Input data not in expected format and dt is missing!")
        t_s = [datetime.now() + timedelta(seconds=i*dt) for i in range(len(data[0]))]
        data = [{'signal': d, 'meta': {'dt': dt}} for d in data]
    else:
        dt = data[0]['meta']['dt']
        t_s = [data[0]['meta']['starttime'] + timedelta(seconds=i*dt) for i in range(len(data[0]['signal']))]

    # Check/set coupling factors
    if coupling is None:
        coupling = [1] * len(data)

    # Check/create aoi
    if aoi is None:
        # Assuming all distance maps have the same shape
        first_map = d_map['maps'][0]  # Changed from d_map['maps'].values()
        aoi = np.ones_like(first_map['values'])  # Assuming 'values' key exists

    # Get maximum possible time delay across distance maps
    d_all = np.concatenate([np.array(d['values']).flatten() * aoi.flatten() for d in d_map['maps']])
    t_diff = np.max(d_all) / v

    if verbose:
        print(f"Maximum possible time delay: {t_diff} s.")

    # Create time window vector
    t_step = np.arange(min(t_s) + timedelta(seconds=t_diff),
                       max(t_s) - timedelta(seconds=t_diff + window),
                       timedelta(seconds=window * (1 - overlap)))

    if verbose:
        print(f"{len(t_step)} windows of {window} s length to process.")

    # Convert distance data sets to matrix with distance values
    d = np.column_stack([aoi.flatten()] + [np.array(d['values']).flatten() for d in d_map['maps']])

    if verbose:
        print(f"{np.sum(aoi)} pixels in AOI to process (total number of pixels: {aoi.size}).")

    # Define model parameters
    model_params = {
        "SurfSpreadAtten": (surf_spread_atten, (f, q, v)),
        "BodySpreadAtten": (body_spread_atten, (f, q, v)),
        "SurfBodySpreadAtten": (surf_body_spread_atten, (f, q, v, k)),
        "SurfSpread": (surf_spread, ()),
        "BodySpread": (body_spread, ()),
        "SurfBodySpread": (surf_body_spread, (k,))
    }

    model_fun, extra_params = model_params[model]

    if verbose:
        print(f"Using model {model}")

    # Detect and adjust number of cores to use
    if cpu is not None:
        n_cpu = int(cpu_count() * cpu)
    else:
        n_cpu = 1

    if verbose:
        print(f"{n_cpu} cores are used.")

    # Process time windows
    results = []
    for j, t_0 in enumerate(t_step):
        if verbose:
            print(f"Processing time step {j+1}/{len(t_step)}...")

        with Pool(n_cpu) as pool:
            results.append(pool.starmap(process_grid, [(d_i, model_fun, extra_params, t_0, data, window, verbose) 
                                                       for d_i in d if d_i[0] == 1]))


    # Restructure output
    l_out = restructure_output(results, t_step)

    # Optionally generate plot output
    if plot:
        plot_results(l_out)

    return l_out

# Update process_grid function to accept extra_params
def process_grid(d_i, model_fun, extra_params, t_0, data, window, verbose):
    """Process a single grid point."""
    t_shift = t_0 + timedelta(seconds=d_i[1:] / data[0]['meta']['v'])
    
    a_window = []
    for i, d in enumerate(data):
        start = (t_shift[i] - d['meta']['starttime']).total_seconds()
        end = start + window
        a_window.append(np.max(d['signal'][int(start/d['meta']['dt']):int(end/d['meta']['dt'])]))

    try:
        popt, _ = curve_fit(lambda d, a_0: model_fun(d, a_0, *extra_params), d_i[1:], a_window, p0=[100 * max(a_window)])
        mod_a_0 = popt[0]
        residuals = a_window - model_fun(d_i[1:], mod_a_0, *extra_params)
        mod_res = np.sqrt(np.mean(residuals**2))
        mod_var = 1 - (np.sum(residuals**2) / np.sum(np.array(a_window)**2))
    except:
        mod_a_0, mod_res, mod_var = np.nan, np.nan, np.nan

    return mod_a_0, mod_res, mod_var

def restructure_output(results, t_step):
    """Restructure the output from parallel processing."""
    df = pd.DataFrame(np.concatenate(results), columns=['a_0', 'res', 'var'])
    
    l_out = {
        'mean': df.mean(),
        'sd': df.std(),
        'q05': df.quantile(0.05),
        'q25': df.quantile(0.25),
        'q50': df.quantile(0.50),
        'q75': df.quantile(0.75),
        'q95': df.quantile(0.95),
        'time': t_step
    }
    
    return l_out

def plot_results(l_out):
    """Plot the results of spatial tracking."""
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5))

    # Plot trajectory
    ax1.errorbar(l_out['mean']['x'], l_out['mean']['y'], 
                 xerr=l_out['sd']['x'], yerr=l_out['sd']['y'],
                 fmt='o', ecolor='gray', capsize=5)
    ax1.set_title('Trajectory')
    ax1.set_xlabel('Easting')
    ax1.set_ylabel('Northing')

    # Plot source amplitude
    ax2.fill_between(l_out['time'], 
                     l_out['mean']['a_0'] - l_out['sd']['a_0'],
                     l_out['mean']['a_0'] + l_out['sd']['a_0'],
                     alpha=0.3)
    ax2.plot(l_out['time'], l_out['mean']['a_0'], 'o-')
    ax2.set_title('Source amplitude')
    ax2.set_xlabel('Time')
    ax2.set_ylabel('Amplitude')

    # Plot variance reduction
    ax3.fill_between(l_out['time'], 
                     100 * (l_out['mean']['var'] - l_out['sd']['var']),
                     100 * (l_out['mean']['var'] + l_out['sd']['var']),
                     alpha=0.3)
    ax3.plot(l_out['time'], 100 * l_out['mean']['var'], 'o-')
    ax3.set_title('Variance reduction')
    ax3.set_xlabel('Time')
    ax3.set_ylabel('Variance reduction (%)')

    plt.tight_layout()
    plt.show()
    
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

if __name__ == "__main__":
    # Example usage
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
        d_map = spatial_distance.spatial_distance(sta, dem_filepath, verbose=True)

        # Print the structure of d_map to verify
        print("Structure of d_map:")
        print(f"Keys: {d_map.keys()}")
        print(f"Type of 'maps': {type(d_map['maps'])}")
        print(f"Length of 'maps': {len(d_map['maps'])}")
        if d_map['maps']:
            print(f"Keys of first map: {d_map['maps'][0].keys()}")

        # seismic data in the correct format
        seismic_data = [
            {'signal': np.random.rand(1000), 'meta': {'dt': 0.01, 'starttime': datetime.now()}},
            {'signal': np.random.rand(1000), 'meta': {'dt': 0.01, 'starttime': datetime.now()}},
            {'signal': np.random.rand(1000), 'meta': {'dt': 0.01, 'starttime': datetime.now()}}
        ]

        result = spatial_track(
            data=seismic_data,
            window=5.0,
            overlap=0.5,
            d_map=d_map,
            v=800,
            q=40,
            f=12,
            qt=0.99,
            verbose=True,
            plot=True
        )

    print(result)