# import

# Import the pre-implemented functions
from pyseis import fmi_parameters, model_bedload, model_turbulence, fmi_spectra

import numpy as np
import matplotlib.pyplot as plt
from concurrent.futures import ProcessPoolExecutor
import multiprocessing
import os
import sys

# Add the parent directory to the path to import custom functions
script_directory = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(script_directory, ".."))


def fmi_inversion(reference, data, n_cores=1):
    """
    Invert fluvial data set based on reference spectra catalogue.

    The fluvial model inversion (FMI) routine uses a predefined look-up table
    with reference spectra to identify those spectra that fit the empirical
    data set best, and returns the corresponding target variables and fit
    errors.

    Note that the frequencies of the empiric and modelled data sets must
    match.

    Parameters:
    -----------
    reference : list
        List containing lists with precalculated model spectra.
    data : numpy.ndarray
        2D array (spectra organised by columns) of empiric spectra which are
        used to identify the best matching target parameters of the reference
        data set.
    n_cores : int, optional
        Number of CPU cores to use. Disabled by setting to 1. Default is 1.

    Returns:
    --------
    dict
        Dictionary containing the inversion results:
        - 'parameters': DataFrame of best fit parameters
        - 'rmse': 2D array of frequency-wise RMSE values

    Examples:
    ---------
    See the main function at the bottom of this script for a usage example.
    """

    # Convert reference spectra and parameters to numpy arrays
    reference_spectra = np.array([x["power"] for x in reference])
    reference_parameters = np.array(
        [list(x["pars"].values()) for x in reference]
        )

    # Function to process a single spectrum
    def process_spectrum(psd):
        if not np.isnan(psd).any():
            d = reference_spectra - psd
            rmse = np.sqrt(np.mean(d**2, axis=1))
            rmse_min = np.min(rmse)
            mod_best = np.argmin(rmse)
            rmse_f = np.sqrt((reference_spectra[mod_best] - psd) ** 2)
        else:
            mod_best = -1  # Use -1 instead of np.nan for invalid spectra
            rmse_f = np.full_like(psd, np.nan)
            rmse_min = np.nan

        return {"rmse_f": rmse_f, "rmse": rmse_min, "mod_best": mod_best}

    # Run the inversion process
    if n_cores > 1:
        with ProcessPoolExecutor(
            max_workers=min(n_cores, multiprocessing.cpu_count())
        ) as executor:
            inversion = list(executor.map(process_spectrum, data.T))
    else:
        inversion = [process_spectrum(psd) for psd in data.T]

    # Extract results
    model_best = np.array([x["mod_best"] for x in inversion])

    # Handle invalid model_best values
    valid_indices = model_best != -1
    if not np.any(valid_indices):
        raise ValueError("No valid spectra found in the input data")

    parameters_out = np.full(
        (len(model_best),
         reference_parameters.shape[1]), np.nan)
    parameters_out[valid_indices] = reference_parameters[
                                        model_best[valid_indices]
                                        ]

    rmse = np.array([x["rmse_f"] for x in inversion])

    return {"parameters": parameters_out, "rmse": rmse}


def main():
    # Create example reference parameter sets
    ref_pars = fmi_parameters.fmi_parameters(
        n=2,
        h_w=[0.02, 2.00],
        q_s=[0.001, 50.000 / 2650],
        d_s=0.01,
        s_s=1.35,
        r_s=2650,
        w_w=6,
        a_w=0.0075,
        f_min=5,
        f_max=80,
        r_0=6,
        f_0=1,
        q_0=10,
        v_0=350,
        p_0=0.55,
        e_0=0.09,
        n_0_a=0.6,
        n_0_b=0.8,
        res=100,
    )

    # Create corresponding reference spectra
    ref_spectra = fmi_spectra.fmi_spectra(parameters=ref_pars, n_cores=2)

    # Define water level and bedload flux time series
    h = np.array([0.01, 1.00, 0.84, 0.60, 0.43, 0.32, 0.24, 0.18, 0.14, 0.11])
    q = np.array([0.05, 5.00, 4.18, 3.01, 2.16, 1.58, 1.18, 0.89, 0.69, 0.54])
    q = q / 2650
    hq = list(zip(h, q))

    # Calculate synthetic spectrogram
    def calculate_psd(hq_pair):
        h, q = hq_pair
        try:
            psd_turbulence = model_turbulence.model_turbulence(
                h_w=h,
                d_s=0.01,
                s_s=1.35,
                r_s=2650,
                w_w=6,
                a_w=0.0075,
                f=(10, 70),
                r_0=5.5,
                f_0=1,
                q_0=18,
                v_0=450,
                p_0=0.34,
                n_0=(0.5, 0.8),
                res=100,
            )["power"]

            psd_bedload = model_bedload.model_bedload(
                h_w=h,
                q_s=q,
                d_s=0.01,
                s_s=1.35,
                r_s=2650,
                w_w=6,
                a_w=0.0075,
                f=(10, 70),
                r_0=5.5,
                f_0=1,
                q_0=18,
                v_0=450,
                x_0=0.34,
                e_0=0.0,
                n_0=0.5,
                res=100,
            )["power"]

            psd_sum = psd_turbulence + psd_bedload
            return 10 * np.log10(psd_sum)
        except Exception as e:
            print(f"Error calculating PSD for h={h}, q={q}: {str(e)}")
            return np.full(100, np.nan)

    psd = np.column_stack([calculate_psd(hq_pair) for hq_pair in hq])

    # Plot synthetic spectrogram
    plt.figure(figsize=(10, 5))
    plt.imshow(psd, aspect="auto", origin="lower", cmap="viridis")
    plt.colorbar(label="PSD (dB)")
    plt.title("Synthetic Spectrogram")
    plt.xlabel("Time step")
    plt.ylabel("Frequency index")
    plt.show()

    # Invert empiric data set
    try:
        result = fmi_inversion(reference=ref_spectra, data=psd)

        # Plot model results
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))

        ax1.plot(result["parameters"][:, 1] * 2650, label="q_s")
        ax1.set_ylabel("Bedload flux (m²/s)")
        ax1.legend()

        ax2.plot(result["parameters"][:, 0], label="h_w")
        ax2.set_ylabel("Water depth (m)")
        ax2.set_xlabel("Time step")
        ax2.legend()

        plt.tight_layout()
        plt.show()
    except Exception as e:
        print(f"Error during inversion: {str(e)}")


if __name__ == "__main__":
    main()
