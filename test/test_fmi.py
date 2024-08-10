import numpy as np
from utils.file_utils import save_csv
from utils.fmi_utils import (
    create_reference_parameters,
    create_reference_spectra,
    calculate_psd,
    perform_inversion
)
from utils.plot_utils import (
    plot_spectra,
    plot_individual_spectra,
    plot_inversion_results
)


def save_reference_parameters(ref_pars):
    """
    Save reference parameters to a CSV file.

    Args:
        ref_pars (list): List of dictionaries containing reference parameters.
    """
    ref_pars_headers = ["Parameter"] + [f"Set {i+1}" for i in range(
        len(ref_pars))]
    ref_pars_data = []
    all_keys = set().union(*ref_pars)
    for key in all_keys:
        row = [key] + [par.get(key, "") for par in ref_pars]
        ref_pars_data.append(row)
    save_csv(ref_pars_data, "Py_fmi_par.csv", headers=ref_pars_headers)


def save_reference_spectra(ref_spectra):
    """
    Save reference spectra to CSV files.

    Args:
        ref_spectra (list): List of dictionaries containing reference spectra.
    """
    for i, spectrum in enumerate(ref_spectra):
        spectrum_data = list(zip(
            spectrum["frequency"],
            spectrum["power"],
            spectrum["turbulence"],
            spectrum["bedload"],
        ))
        save_csv(
            spectrum_data,
            f"Py_fmi_ref_spectrum_{i+1}.csv",
            headers=["Frequency", "Power", "Turbulence", "Bedload"],
        )


def print_spectra_info(ref_spectra):
    """
    Print information about the calculated spectra.

    Args:
        ref_spectra (list): List of dictionaries containing reference spectra.
    """
    print(f"Number of spectra calculated: {len(ref_spectra)}")
    for i, spectrum in enumerate(ref_spectra):
        print(f"\nSpectrum {i+1}:")
        print(f"  Water depth: {spectrum['pars']['h_w']} m")
        print(f"  Sediment flux: {spectrum['pars']['q_s']} m^2/s")

        if "frequency" in spectrum:
            if isinstance(
                spectrum["frequency"], (list, np.ndarray)
                 ) and len(spectrum["frequency"]) > 0:
                print(f"  Frequency range: {spectrum['frequency'][0]} \
                    - {spectrum['frequency'][-1]} Hz")
            else:
                print(f"  Frequency: {spectrum['frequency']}")
        else:
            print("  Frequency data not available")

        if "power" in spectrum:
            if isinstance(
                 spectrum["power"], (list, np.ndarray)
                 ) and len(spectrum["power"]) > 0:
                print(f"  Power range: {min(spectrum['power']):.2f} \
                    - {max(spectrum['power']):.2f} dB")
            else:
                print(f"  Power: {spectrum['power']}")
        else:
            print("  Power data not available")


def create_synthetic_spectrogram():
    """
    Create a synthetic spectrogram using predefined water depth
    and sediment flux values.

    Returns:
        numpy.ndarray: A 2D array representing the synthetic spectrogram.
    """
    h = np.array([0.01, 1.00, 0.84, 0.60, 0.43, 0.32, 0.24, 0.18, 0.14, 0.11])
    q = np.array(
        [0.05, 5.00, 4.18, 3.01, 2.16, 1.58, 1.18, 0.89, 0.69, 0.54]
        ) / 2650
    hq = list(zip(h, q))
    return np.column_stack([calculate_psd(hq_pair) for hq_pair in hq])


def run_inversion(ref_spectra, psd):
    """
    Run the inversion process and plot the results.

    Args:
        ref_spectra (list): List of dictionaries containing reference spectra.
        psd (numpy.ndarray): Power spectral density data.
    """
    try:
        result = perform_inversion(ref_spectra, psd)
        plot_inversion_results(result)
    except Exception as e:
        print(f"Error during inversion or plotting: {str(e)}")


def main():
    """
    Main function to test FMI (Fluvial Monitor Inversion) and model functions.

    This function performs the following tasks:
    1. Creates example reference parameter sets
    2. Generates corresponding reference spectra
    3. Plots and saves the generated spectra
    4. Defines water level and bedload flux time series
    5. Calculates and plots a synthetic spectrogram
    6. Inverts empiric data set and plots RMSE per frequency

    All plots and results are saved in the 'output' folder.
    """
    # Create example reference parameter sets
    ref_pars = create_reference_parameters()
    save_reference_parameters(ref_pars)

    # Create corresponding reference spectra
    ref_spectra = create_reference_spectra(ref_pars)
    save_reference_spectra(ref_spectra)

    # Print results
    print_spectra_info(ref_spectra)

    # Plotting
    plot_spectra(ref_spectra)
    plot_individual_spectra(ref_spectra)

    # Calculate synthetic spectrogram
    psd = create_synthetic_spectrogram()

    # Invert empiric data set
    run_inversion(ref_spectra, psd)


if __name__ == "__main__":
    main()
