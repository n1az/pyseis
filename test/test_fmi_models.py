from pyseis import (
    fmi_parameters,
    model_bedload,
    model_turbulence,
    fmi_spectra,
    fmi_inversion,
)
import numpy as np
import matplotlib.pyplot as plt
import os
import csv

# Create output directory path
script_directory = os.path.dirname(os.path.realpath(__file__))
output_dir = os.path.join(script_directory, "output")
os.makedirs(output_dir, exist_ok=True)

# Import the pre-implemented functions


def save_plot(fig, filename):
    """
    Save the given figure to the output folder.

    Args:
        fig (matplotlib.figure.Figure): The figure to save.
        filename (str): The name of the file to save the figure as.
    """
    fig.savefig(os.path.join(output_dir, filename))


def save_csv(data, filename, headers=None):
    """
    Save the given data to a CSV file in the output folder.

    Args:
        data (list): The data to save.
        filename (str): The name of the file to save the data as.
        headers (list, optional): The headers for the CSV file.
    """
    with open(os.path.join(output_dir, filename), "w", newline="") as f:
        writer = csv.writer(f)
        if headers:
            writer.writerow(headers)
        writer.writerows(data)


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

    # Save ref_pars to CSV
    ref_pars_headers = ["Parameter"] + \
        [f"Set {i+1}" for i in range(len(ref_pars))]
    ref_pars_data = []

    # Get all unique keys from all dictionaries
    all_keys = set().union(*ref_pars)

    for key in all_keys:
        row = [key] + [par.get(key, "") for par in ref_pars]
        ref_pars_data.append(row)

    save_csv(ref_pars_data, "Py_fmi_par.csv", headers=ref_pars_headers)

    # Create corresponding reference spectra
    ref_spectra = fmi_spectra.fmi_spectra(parameters=ref_pars, n_cores=2)

    # Save ref_spectra to CSV
    for i, spectrum in enumerate(ref_spectra):
        spectrum_data = list(
            zip(
                spectrum["frequency"],
                spectrum["power"],
                spectrum["turbulence"],
                spectrum["bedload"],
            )
        )
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
                    f"  Power range: {min(spectrum['power']):.2f} - \
                        {max(spectrum['power']):.2f} dB"
                )
            else:
                print(f"  Power: {spectrum['power']}")
        else:
            print("  Power data not available")

    # Plotting
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
    save_plot(plt.gcf(), "Py_fmi_spectra.png")
    plt.close()

    # Plot individual spectra
    for i, spectrum in enumerate(ref_spectra):
        plt.figure(figsize=(10, 6))
        plt.plot(spectrum["frequency"], spectrum["power"], label="Combined")
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
            f'Spectrum {i+1} (h_w: {spectrum["pars"]["h_w"]:.2f} m, q_s: \
                {spectrum["pars"]["q_s"]:.6f} m^2/s)'
        )
        plt.legend()
        plt.xscale("log")
        plt.grid(True)
        plt.tight_layout()
        save_plot(plt.gcf(), f"Py_fmi_spectrum_{i+1}.png")
        plt.close()

    # Define water level and bedload flux time series
    h = np.array([0.01, 1.00, 0.84, 0.60, 0.43, 0.32, 0.24, 0.18, 0.14, 0.11])
    q = np.array([0.05, 5.00, 4.18, 3.01, 2.16, 1.58,
                 1.18, 0.89, 0.69, 0.54]) / 2650
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

    # Save synthetic spectrogram data to CSV
    # save_csv(psd, 'Py_fmi_syn_spect.csv')

    # Invert empiric data set
    try:
        result = fmi_inversion.fmi_inversion(reference=ref_spectra, data=psd)

        # Plot model results
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))

        ax1.plot(result["parameters"][:, 1] * 2650, label="q_s")
        ax1.set_ylabel("Bedload flux (m²/s)")
        ax1.legend()

        ax2.plot(result["parameters"][:, 0], label="h_w")
        ax2.set_ylabel("Water depth (m)")
        ax2.set_xlabel("Time step")
        ax2.legend()
        save_plot(fig, "Py_fmi_inversion.png")
        plt.tight_layout()
        plt.close()

    except Exception as e:
        print(f"Error during inversion or plotting: {str(e)}")


if __name__ == "__main__":
    main()
