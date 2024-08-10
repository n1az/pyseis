"""
    This module contains utility functions, and is not a component.
"""

import matplotlib.pyplot as plt
from utils.file_utils import save_plot


def plot_spectra(ref_spectra):
    """
    Plot all reference spectra.

    Args:
        ref_spectra (list): A list of spectrum dictionaries.
    """
    plt.figure(figsize=(12, 8))
    for i, spectrum in enumerate(ref_spectra):
        plt.plot(spectrum["frequency"],
                 spectrum["power"],
                 label=f"Spectrum {i+1}")
        plt.plot(spectrum["frequency"],
                 spectrum["turbulence"],
                 label=f"Turbulence {i+1}",
                 linestyle="--")
        plt.plot(spectrum["frequency"],
                 spectrum["bedload"],
                 label=f"Bedload {i+1}",
                 linestyle=":")

    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Power Spectral Density (dB)")
    plt.title("FMI Spectra")
    plt.legend()
    plt.xscale("log")
    plt.grid(True)
    plt.tight_layout()
    save_plot(plt.gcf(), "Py_fmi_spectra.png")
    plt.close()


def plot_individual_spectra(ref_spectra):
    """
    Plot individual spectra.

    Args:
        ref_spectra (list): A list of spectrum dictionaries.
    """
    for i, spectrum in enumerate(ref_spectra):
        plt.figure(figsize=(10, 6))
        plt.plot(spectrum["frequency"],
                 spectrum["power"],
                 label="Combined")
        plt.plot(spectrum["frequency"],
                 spectrum["turbulence"],
                 label="Turbulence",
                 linestyle="--")
        plt.plot(spectrum["frequency"],
                 spectrum["bedload"],
                 label="Bedload",
                 linestyle=":")
        plt.xlabel("Frequency (Hz)")
        plt.ylabel("Power Spectral Density (dB)")
        plt.title(f'Spectrum {i+1} (h_w: {spectrum["pars"]["h_w"]:.2f} m,\
            q_s: {spectrum["pars"]["q_s"]:.6f} m^2/s)')
        plt.legend()
        plt.xscale("log")
        plt.grid(True)
        plt.tight_layout()
        save_plot(plt.gcf(), f"Py_fmi_spectrum_{i+1}.png")
        plt.close()


def plot_inversion_results(result):
    """
    Plot inversion results.

    Args:
        result (dict): The inversion results.
    """
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


def plot_dem_with_stations(dem, sta, sta_ids):
    fig, ax = plt.subplots(figsize=(10, 10))
    dem_data = dem.read(1)
    dem_bounds = dem.bounds
    im = ax.imshow(
        dem_data,
        extent=(dem_bounds.left,
                dem_bounds.right,
                dem_bounds.bottom,
                dem_bounds.top),
        origin="lower",
        cmap="terrain",
    )
    for i, (x, y) in enumerate(sta):
        ax.plot(x, y, "ro")
        ax.text(x,
                y,
                sta_ids[i],
                color="white",
                fontsize=12,
                ha="right",
                va="bottom")
    plt.colorbar(im, label="Elevation")
    ax.set_title("DEM with Station Locations")
    ax.set_xlabel("X coordinate")
    ax.set_ylabel("Y coordinate")
    save_plot(fig, "Py_spatial_dist_0.png")
    plt.close()


def plot_distance_matrix(result, sta_ids):
    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(result["matrix"], cmap="viridis")
    plt.colorbar(im, label="Distance")
    ax.set_title("Distance Matrix between Stations")
    ax.set_xlabel("Station Index")
    ax.set_ylabel("Station Index")
    for i in range(len(sta_ids)):
        for j in range(len(sta_ids)):
            ax.text(j,
                    i,
                    f"{result['matrix'][i, j]:.2f}",
                    ha="center",
                    va="center",
                    color="white")
    plt.tight_layout()
    save_plot(fig, "Py_spatial_dist_mat.png")
    plt.close()


def plot_distance_maps(result, dem_bounds, sta, sta_ids):
    fig, axs = plt.subplots(1, len(sta), figsize=(5 * len(sta), 5))
    if len(sta) == 1:
        axs = [axs]
    for i, map_data in enumerate(result["maps"]):
        if map_data is not None:
            im = axs[i].imshow(
                map_data["values"],
                cmap="viridis",
                extent=(dem_bounds.left,
                        dem_bounds.right,
                        dem_bounds.bottom,
                        dem_bounds.top),
                origin="lower",
            )
            axs[i].set_title(f"Distance Map for Station {sta_ids[i]}")
            plt.colorbar(im, ax=axs[i], label="Distance")
            axs[i].plot(sta[i, 0], sta[i, 1], "ro", markersize=10)
            axs[i].text(sta[i, 0],
                        sta[i, 1],
                        sta_ids[i],
                        color="white",
                        fontsize=12,
                        ha="right",
                        va="bottom")
    plt.tight_layout()
    save_plot(fig, "distance_maps.png")
    plt.close()


def plot_spatial_amplitude(e, dem_bounds, e_max_list, sta, sta_ids):
    fig, ax = plt.subplots(figsize=(10, 10))
    with e.open() as dataset:
        e_data = dataset.read(1)
        im = ax.imshow(
            e_data,
            extent=(dem_bounds.left,
                    dem_bounds.right,
                    dem_bounds.bottom,
                    dem_bounds.top),
            origin="lower",
            cmap="viridis",
        )
        plt.colorbar(im, label="Amplitude")

        if e_max_list:
            for i, e_max in enumerate(e_max_list):
                ax.plot(e_max[0],
                        e_max[1],
                        "ro",
                        markersize=10,
                        label=f"Max Amplitude {i+1}" if i == 0 else "")
            for i, (x, y) in enumerate(sta):
                ax.plot(x, y, "bo", markersize=8)
                ax.text(x,
                        y,
                        sta_ids[i],
                        color="white",
                        fontsize=12,
                        ha="right",
                        va="bottom")
            ax.set_title("Spatial Amplitude and Most Likely Location(s)")
            ax.set_xlabel("X coordinate")
            ax.set_ylabel("Y coordinate")
            ax.legend()
            save_plot(fig, "Py_spatial_amp.png")
            plt.close()
        else:
            print("No maximum amplitude points found.")


def plot_migration_results(migrated_result,
                           clipped_result,
                           dem_bounds,
                           sta,
                           sta_ids):
    # Plot original migrated result
    fig, ax = plt.subplots(figsize=(10, 10))
    migrated_data = migrated_result.read(1)
    im1 = ax.imshow(
        migrated_data,
        extent=(dem_bounds.left,
                dem_bounds.right,
                dem_bounds.bottom,
                dem_bounds.top),
        origin="lower",
        cmap="viridis",
    )
    plt.colorbar(im1, ax=ax, label="Migration Value")
    ax.set_title("Original Spatial Migration Result")
    ax.set_xlabel("X coordinate")
    ax.set_ylabel("Y coordinate")
    for i, (x, y) in enumerate(sta):
        ax.plot(x, y, "ro", markersize=8)
        ax.text(x,
                y,
                sta_ids[i],
                color="white",
                fontsize=12,
                ha="right",
                va="bottom")
    save_plot(fig, "Py_spatial_migration.png")
    plt.close()

    # Plot clipped migrated result
    fig, ax = plt.subplots(figsize=(10, 10))
    clipped_data = clipped_result.read(1)
    im2 = ax.imshow(
        clipped_data,
        extent=(dem_bounds.left,
                dem_bounds.right,
                dem_bounds.bottom,
                dem_bounds.top),
        origin="lower",
        cmap="viridis",
    )
    plt.colorbar(im2, ax=ax, label="Clipped Migration Value")
    ax.set_title("Clipped Spatial Migration Result (75th percentile)")
    ax.set_xlabel("X coordinate")
    ax.set_ylabel("Y coordinate")
    for i, (x, y) in enumerate(sta):
        ax.plot(x, y, "ro", markersize=8)
        ax.text(x,
                y,
                sta_ids[i],
                color="white",
                fontsize=12,
                ha="right",
                va="bottom")
    plt.tight_layout()
    save_plot(fig, "Py_spatial_clipped.png")
    plt.close()

    return migrated_data, clipped_data
