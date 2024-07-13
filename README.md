<h1 align="center">Pyseis</h1>

<p align="center">
  <a href="#dart-project-overview">Overview</a> &#xa0; | &#xa0; 
  <a href="#sparkles-features">Features</a> &#xa0; | &#xa0;
  <a href="#rocket-tools">Tools</a> &#xa0; | &#xa0;
  <a href="#white_check_mark-installation">Installation</a> &#xa0; | &#xa0;
  <a href="#memo-license">License</a> &#xa0; | &#xa0;
  <a href="#black_nib-citation">Citation</a> &#xa0; | &#xa0;
  <a href="#notebook_with_decorative_cover-contributing-to-pyseis">Contributions</a> &#xa0; | &#xa0;
</p>


## :dart: Project Overview ##

PySeis is a `Python` package for environmental seismology, a scientific field that studies the seismic signals emitted by Earth surface processes. This package provides a suite of tools to facilitate the reading, writing, preparation, analysis, and visualization of seismic data, drawing inspiration from the functionality of the [eseis](R/dietze2018_R_eseis.pdf) package in `R`. 

## :question: Why Pyseis ##

While the eseis package in `R` offers tools for seismological data analysis, there was a gap in equivalent functionality within the `Python` ecosystem. PySeis aims to bridge this gap by providing `Python` users with a comparable suite of tools, ensuring they can perform environmental seismology tasks efficiently within a `Python` environment.

## :sparkles: Features ##

:heavy_check_mark: Fluvial data inversion\
:heavy_check_mark: Reference model creation\
:heavy_check_mark: Spatial distance calculation\
:heavy_check_mark: Spatial signals migration\
:heavy_check_mark: Spatial data clipping\
:heavy_check_mark: Coordinate conversion\
:heavy_check_mark: Source location detection\
:heavy_check_mark: Source tracking\
:heavy_check_mark: Spectrum modeling

## :rocket: Tools ##

The following tools were used in this project:

- [Python](https://www.python.org)
- [NumPy](https://pypi.org/project/numpy/)
- [Pandas](https://pypi.org/project/pandas/)
- [Geopandas](https://pypi.org/project/geopandas/)
- [Matplotlib](https://pypi.org/project/matplotlib/)
- [Scipy](https://pypi.org/project/scipy/)
- [Shapely](https://pypi.org/project/shapely/)
- [Rasterio](https://pypi.org/project/rasterio/)




## :white_check_mark: Installation ##

Before starting :checkered_flag:, you need to have [Git](https://git-scm.com) and [Python](https://www.python.org) installed.

## :checkered_flag: Starting ##

```bash
# Clone this project
$ git clone https://github.com/{{YOUR_GITHUB_USERNAME}}/pyseis

# Access
$ cd pyseis

# Install dependencies
$ pip install -r requirements.txt

# Run the project
$ python pyseis.py

```

## :memo: License ##

[MIT](LICENSE)

## :black_nib: Citation ##

If you use this software, please cite it using [this](CITATION.cff) file.

## :notebook_with_decorative_cover: Contributing to Pyseis ##

[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg)](CONDUCT.md)

All contributions, bug reports, bug fixes, documentation improvements, enhancements, and ideas are welcome.

A detailed overview on how to contribute can be found in the [contributing guide](CONTRIBUTING.md). Feel free to create new issues and start working on it!

As contributors and maintainers to this project, you are expected to abide by Pyseis' code of conduct. 

More information can be found at: [Code of Conduct](CONDUCT.md)

&#xa0;

<a href="#top">Back to top</a>
