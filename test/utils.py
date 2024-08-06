import os
import csv

# Create output directory path
script_directory = os.path.dirname(os.path.realpath(__file__))
output_dir = os.path.join(script_directory, "output")
os.makedirs(output_dir, exist_ok=True)


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
