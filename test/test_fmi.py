import os
import numpy as np
from parameters import create_reference_parameters
from spectra import create_reference_spectra
from models import calculate_psd
from plot_utils import plot_spectra, plot_individual_spectra
from plot_utils import plot_inversion_results
from file_io import save_reference_parameters, save_reference_spectra
from pyseis import fmi_inversion


def main():
    script_directory = os.path.dirname(os.path.realpath(__file__))
    output_dir = os.path.join(script_directory, "output")
    os.makedirs(output_dir, exist_ok=True)

    ref_pars = create_reference_parameters()
    save_reference_parameters(ref_pars, output_dir)

    ref_spectra = create_reference_spectra(ref_pars)
    save_reference_spectra(ref_spectra, output_dir)

    print(f"Number of spectra calculated: {len(ref_spectra)}")
    for i, spectrum in enumerate(ref_spectra):
        print(f"\nSpectrum {i+1}:")
        print(f"  Water depth: {spectrum['pars']['h_w']} m")
        print(f"  Sediment flux: {spectrum['pars']['q_s']} m^2/s")

        if "frequency" in spectrum:
            if (
                isinstance(spectrum["frequency"], (list, np.ndarray))
                and len(spectrum["frequency"]) > 0
            ):
                print(
                    f"  Frequency range: {spectrum['frequency'][0]} \
                        - {spectrum['frequency'][-1]} Hz"
                )
            else:
                print(f"  Frequency: {spectrum['frequency']}")
        else:
            print("  Frequency data not available")

        if "power" in spectrum:
            if (
                isinstance(spectrum["power"], (list, np.ndarray))
                and len(spectrum["power"]) > 0
            ):
                print(
                    f"  Power range: {min(spectrum['power']):.2f} \
                        - {max(spectrum['power']):.2f} dB"
                )
            else:
                print(f"  Power: {spectrum['power']}")
        else:
            print("  Power data not available")

    plot_spectra(ref_spectra, output_dir)
    plot_individual_spectra(ref_spectra, output_dir)

    h = np.array(
        [0.01, 1.00, 0.84, 0.60, 0.43, 0.32, 0.24, 0.18, 0.14, 0.11]
        )
    q = np.array(
        [0.05, 5.00, 4.18, 3.01, 2.16, 1.58, 1.18, 0.89, 0.69, 0.54]
        ) / 2650
    hq = list(zip(h, q))
    psd = np.column_stack([calculate_psd(hq_pair) for hq_pair in hq])

    try:
        result = fmi_inversion.fmi_inversion(reference=ref_spectra, data=psd)
        plot_inversion_results(result, output_dir)
    except Exception as e:
        print(f"Error during inversion or plotting: {str(e)}")


if __name__ == "__main__":
    main()
