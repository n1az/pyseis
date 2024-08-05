import matplotlib.pyplot as plt
import os


def save_plot(fig, filename, output_dir):
    fig.savefig(os.path.join(output_dir, filename))


def plot_spectra(ref_spectra, output_dir):
    plt.figure(figsize=(12, 8))
    for i, spectrum in enumerate(ref_spectra):
        plt.plot(
            spectrum["frequency"],
            spectrum["power"],
            label=f"Spectrum {i+1}"
        )
        plt.plot(
            spectrum["frequency"],
            spectrum["turbulence"],
            label=f"Turbulence {i+1}",
            linestyle="--"
        )
        plt.plot(
            spectrum["frequency"],
            spectrum["bedload"],
            label=f"Bedload {i+1}",
            linestyle=":"
        )

    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Power Spectral Density (dB)")
    plt.title("FMI Spectra")
    plt.legend()
    plt.xscale("log")
    plt.grid(True)
    plt.tight_layout()
    save_plot(plt.gcf(), "Py_fmi_spectra.png", output_dir)
    plt.close()


def plot_individual_spectra(ref_spectra, output_dir):
    for i, spectrum in enumerate(ref_spectra):
        plt.figure(figsize=(10, 6))
        plt.plot(
            spectrum["frequency"],
            spectrum["power"],
            label="Combined"
        )
        plt.plot(
            spectrum["frequency"],
            spectrum["turbulence"],
            label="Turbulence",
            linestyle="--"
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
            f'Spectrum {i+1} (h_w: {spectrum["pars"]["h_w"]:.2f} m,\
                q_s: {spectrum["pars"]["q_s"]:.6f} m^2/s)')
        plt.legend()
        plt.xscale("log")
        plt.grid(True)
        plt.tight_layout()
        save_plot(plt.gcf(), f"Py_fmi_spectrum_{i+1}.png", output_dir)
        plt.close()


def plot_inversion_results(result, output_dir):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))
    ax1.plot(result["parameters"][:, 1] * 2650, label="q_s")
    ax1.set_ylabel("Bedload flux (m²/s)")
    ax1.legend()
    ax2.plot(result["parameters"][:, 0], label="h_w")
    ax2.set_ylabel("Water depth (m)")
    ax2.set_xlabel("Time step")
    ax2.legend()
    save_plot(fig, "Py_fmi_inversion.png", output_dir)
    plt.tight_layout()
    plt.close()
