import argparse
import numpy as np
from concurrent.futures import ProcessPoolExecutor
import multiprocessing
import matplotlib.pyplot as plt
from pyseis import fmi_parameters, model_bedload, model_turbulence


def f(parameters):
    # Model spectrum due to water flow
    p_turbulence = model_turbulence.model_turbulence(
        d_s=parameters["d_s"],
        s_s=parameters["s_s"],
        r_s=parameters["r_s"],
        h_w=parameters["h_w"],
        w_w=parameters["w_w"],
        a_w=parameters["a_w"],
        f=[parameters["f_min"], parameters["f_max"]],
        r_0=parameters["r_0"],
        f_0=parameters["f_0"],
        q_0=parameters["q_0"],
        v_0=parameters["v_0"],
        p_0=parameters["p_0"],
        n_0=[parameters["n_0_a"], parameters["n_0_b"]],
        res=parameters["res"],
    )

    # Model spectrum due to bedload impacts
    p_bedload = model_bedload.model_bedload(
        d_s=parameters["d_s"],
        s_s=parameters["s_s"],
        r_s=parameters["r_s"],
        q_s=parameters["q_s"],
        h_w=parameters["h_w"],
        w_w=parameters["w_w"],
        a_w=parameters["a_w"],
        f=[parameters["f_min"], parameters["f_max"]],
        r_0=parameters["r_0"],
        f_0=parameters["f_0"],
        q_0=parameters["q_0"],
        e_0=parameters["e_0"],
        v_0=parameters["v_0"],
        x_0=parameters["p_0"],
        n_0=parameters["n_0_a"],
        res=parameters["res"],
    )

    # Combine model outputs
    p_combined = p_turbulence.copy()
    p_combined["spectrum"] = p_turbulence["power"] + p_bedload["power"]

    # Convert linear to log scale
    p_turbulence_log = p_turbulence.copy()
    p_bedload_log = p_bedload.copy()
    p_combined_log = p_combined.copy()

    p_turbulence_log["power"] = 10 * np.log10(p_turbulence["power"])
    p_bedload_log["power"] = 10 * np.log10(p_bedload["power"])
    p_combined_log["power"] = 10 * np.log10(p_combined["power"])

    # Return model outputs
    return {
        "pars": parameters,
        "frequency": p_combined_log["frequency"],
        "power": p_combined_log["power"],
        "turbulence": p_turbulence_log["power"],
        "bedload": p_bedload_log["power"],
    }


def fmi_spectra(parameters, n_cores=1):
    """
    Create reference model spectra catalogue for
    fluvial model inversion (FMI) routine.

    This function calculates reference spectra based
    on predefined model parameters.
    It can utilize multiple CPU cores for parallel processing.

    Parameters:
    -----------
    parameters : list of dict
        List containing dictionaries with model parameters for
        which the spectra shall be calculated.
    n_cores : int, optional
        Number of CPU cores to use. Parallel processing is disabled
        by setting to 1. Default is 1.

    Returns:
    --------
    list of dict
        List of dictionaries containing the calculated reference spectra and
        the corresponding input parameters. The spectra are given in dB for
        seamless comparison with the empirical PSD data, while the original
        output of the models are in linear scale.

    Notes:
    ------
    This function requires the implementation of `model_turbulence` and
    `model_bedload` functions, which should be imported from another module.

    Example:
    --------
    >>> ref_pars = fmi_parameters(n=2, h_w=[0.02, 2.00], ...)
    >>> ref_spectra = fmi_spectra(parameters=ref_pars, n_cores=4)
    """
    if n_cores > 1:
        n_cores_system = multiprocessing.cpu_count()
        n_cores = min(n_cores, n_cores_system)

        with ProcessPoolExecutor(max_workers=n_cores) as executor:
            spectra = list(executor.map(f, parameters))
    else:
        spectra = [f(param) for param in parameters]

    return spectra


if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description='Reference model spectra example.')
    parser.add_argument(
        '--show-plot',
        action='store_true',
        help='Show the plot of the results')

    # Parse command line arguments
    args = parser.parse_args()

    # Example usage
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
    ref_spectra = fmi_spectra(parameters=ref_pars, n_cores=2)

    # Print results
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
                    f"  Frequency range: {spectrum['frequency'][0]} - \
                        {spectrum['frequency'][-1]} Hz"
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
                    f"  Power range: {min(spectrum['power']):.2f} - \
                        {max(spectrum['power']):.2f} dB"
                )
            else:
                print(f"  Power: {spectrum['power']}")
        else:
            print("  Power data not available")

    # Plotting
    if args.show_plot:
        plt.figure(figsize=(12, 8))
        for i, spectrum in enumerate(ref_spectra):
            plt.plot(
                spectrum["frequency"],
                spectrum["power"],
                label=f"Spectrum {i+1}")
            plt.plot(
                spectrum["frequency"],
                spectrum["turbulence"],
                label=f"Turbulence {i+1}",
                linestyle="--",
            )
            plt.plot(
                spectrum["frequency"],
                spectrum["bedload"],
                label=f"Bedload {i+1}",
                linestyle=":",
            )

        plt.xlabel("Frequency (Hz)")
        plt.ylabel("Power Spectral Density (dB)")
        plt.title("FMI Spectra")
        plt.legend()
        plt.xscale("log")
        plt.grid(True)
        plt.tight_layout()
        plt.show()

        # Plot individual spectra
        for i, spectrum in enumerate(ref_spectra):
            plt.figure(figsize=(10, 6))
            plt.plot(
                spectrum["frequency"],
                spectrum["power"],
                label="Combined")
            plt.plot(
                spectrum["frequency"],
                spectrum["turbulence"],
                label="Turbulence",
                linestyle="--",
            )
            plt.plot(
                spectrum["frequency"],
                spectrum["bedload"],
                label="Bedload",
                linestyle=":"
            )
            plt.xlabel("Frequency (Hz)")
            plt.ylabel("Power Spectral Density (dB)")
            plt.title(
                f'Spectrum {i+1} (h_w: {spectrum["pars"]["h_w"]:.2f} \
                    m, q_s: {spectrum["pars"]["q_s"]:.6f} m^2/s)'
            )
            plt.legend()
            plt.xscale("log")
            plt.grid(True)
            plt.tight_layout()
            plt.show()
    else:
        print("Skipping FMI Spectra plot display")
