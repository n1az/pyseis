import numpy as np
from utils import save_csv
from fmi_analysis import (
    create_reference_parameters,
    create_reference_spectra,
    calculate_psd,
    perform_inversion
)
from plot_utils import (
    plot_spectra,
    plot_individual_spectra,
    plot_inversion_results
)


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

    # Save ref_pars to CSV
    ref_pars_headers = ["Parameter"] + [f"Set {i+1}" for i in range(
        len(ref_pars))]
    ref_pars_data = []

    # Get all unique keys from all dictionaries
    all_keys = set().union(*ref_pars)

    for key in all_keys:
        row = [key] + [par.get(key, "") for par in ref_pars]
        ref_pars_data.append(row)

    save_csv(ref_pars_data, "Py_fmi_par.csv", headers=ref_pars_headers)

    # Create corresponding reference spectra
    ref_spectra = create_reference_spectra(ref_pars)

    # Save ref_spectra to CSV
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

    # Print results
    print(f"Number of spectra calculated: {len(ref_spectra)}")
    for i, spectrum in enumerate(ref_spectra):
        print(f"\nSpectrum {i+1}:")
        print(f"  Water depth: {spectrum['pars']['h_w']} m")
        print(f"  Sediment flux: {spectrum['pars']['q_s']} m^2/s")

        if "frequency" in spectrum:
            if isinstance(spectrum["frequency"], (list, np.ndarray)) and len(
                 spectrum["frequency"]) > 0:
                print(f"  Frequency range: {spectrum['frequency'][0]} \
                    - {spectrum['frequency'][-1]} Hz")
            else:
                print(f"  Frequency: {spectrum['frequency']}")
        else:
            print("  Frequency data not available")

        if "power" in spectrum:
            if isinstance(spectrum["power"], (list, np.ndarray)) and len(
                 spectrum["power"]) > 0:
                print(f"  Power range: {min(spectrum['power']):.2f} \
                    - {max(spectrum['power']):.2f} dB")
            else:
                print(f"  Power: {spectrum['power']}")
        else:
            print("  Power data not available")

    # Plotting
    plot_spectra(ref_spectra)
    plot_individual_spectra(ref_spectra)

    # Define water level and bedload flux time series
    h = np.array([0.01, 1.00, 0.84, 0.60, 0.43, 0.32, 0.24, 0.18, 0.14, 0.11])
    q = np.array(
        [0.05, 5.00, 4.18, 3.01, 2.16, 1.58, 1.18, 0.89, 0.69, 0.54]
        ) / 2650
    hq = list(zip(h, q))

    # Calculate synthetic spectrogram
    psd = np.column_stack([calculate_psd(hq_pair) for hq_pair in hq])

    # Save synthetic spectrogram data to CSV
    # save_csv(psd, 'Py_fmi_syn_spect.csv')

    # Invert empiric data set
    try:
        result = perform_inversion(ref_spectra, psd)
        plot_inversion_results(result)
    except Exception as e:
        print(f"Error during inversion or plotting: {str(e)}")


if __name__ == "__main__":
    main()
