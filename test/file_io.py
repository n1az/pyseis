import csv
import os


def save_csv(data, filename, headers=None, output_dir="."):
    with open(os.path.join(output_dir, filename), "w", newline="") as f:
        writer = csv.writer(f)
        if headers:
            writer.writerow(headers)
        writer.writerows(data)


def save_reference_parameters(ref_pars, output_dir):
    ref_pars_headers = ["Parameter"] + [f"Set {i+1}"
                                        for i in range(len(ref_pars))]
    ref_pars_data = []
    all_keys = set().union(*ref_pars)
    for key in all_keys:
        row = [key] + [par.get(key, "") for par in ref_pars]
        ref_pars_data.append(row)
    save_csv(
        ref_pars_data,
        "Py_fmi_par.csv",
        headers=ref_pars_headers,
        output_dir=output_dir
    )


def save_reference_spectra(ref_spectra, output_dir):
    for i, spectrum in enumerate(ref_spectra):
        spectrum_data = list(zip(
            spectrum["frequency"],
            spectrum["power"],
            spectrum["turbulence"],
            spectrum["bedload"]
        ))
        save_csv(
            spectrum_data,
            f"Py_fmi_ref_spectrum_{i+1}.csv",
            headers=["Frequency", "Power", "Turbulence", "Bedload"],
            output_dir=output_dir
        )
