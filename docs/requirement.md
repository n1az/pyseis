# Pyseis
## Functional Requirements

### Abstract Description

The data analysis workflow is designed to facilitate the translation and validation of seismological data analysis components from the R programming language to Python. This workflow ensures that the translated components are functionally equivalent to their original counterparts by comparing the outputs from both implementations. Below is an abstract description of each step in the workflow:

### Component Selection
Identify and select specific components from the existing `eseis` package, which is used for seismological data analysis in R. We only selected the components which are not currently available in Python.

### Translation to Python
Translate the selected R components into Python, ensuring that the functionality and logic of the original components are preserved.

### Unit Testing
Conduct unit testing on the translated Python components to verify their correctness and ensure they perform as expected.

### Output Generation
Generate outputs using both the translated Python components and the original R components. This step is performed in parallel to maintain efficiency.

### Output Comparison
Compare the outputs generated from the Python and R implementations to check for consistency and accuracy.

### Validation Decision
Evaluate whether the outputs from both implementations match:
- **If the outputs match**: The workflow concludes successfully, indicating that the translated Python components are functionally equivalent to the original R components.
- **If the outputs do not match**: Debug the translated components, identify discrepancies, and reiterate the translation process until the outputs match.

### Debug and Reiterate
If discrepancies are found during the output comparison, debug the translated Python components. This involves analyzing the differences, correcting any issues, and repeating the translation and validation steps until consistency is achieved.

## UML Activity Diagram

Below is the PlantUML code for the described activity diagram, incorporating the loop back to the translation step using the `repeat` syntax:

![Activity Diagram](diagram_updated.png)

## Component Analysis
| Abstract Workflow Node | Operation | Input(s) | Output(s) | Implementation |
| --- | --- | --- | --- | --- |
| **Model Creation** | | | | | |
| fmi_inversion | Invert fluvial data set based on reference spectra catalogue | reference list, seismic dataset, number of cores | list containing the inversion results | Frieder |
| fmi_parameters | Create reference model reference parameter catalogue | numerical values of ground, river and topographical parameters | list with with model reference parameters | Frieder |
| **Data Inversion** | | | | | |
| fmi_spectra | Create reference model spectra catalogue | list with model parameters, number of cores | list containing input parameters and calculated reference spectra |  Frieder|
| **Seismic Distance Calculation** | | | | | |
| spatial_distance | Calculate topography-corrected distances for seismic waves | ***stations:*** Numeric matrix of length two, x- and y-coordinates of the seismic stations <br> ***dem:*** SpatRaster object, the digital elevation model (DEM) to be processed <br> ***topography:*** Logical scalar, option to enable topography correction <br> ***maps:*** Logical scalar, option to enable/disable calculation of distance maps <br> ***matrix:*** Logical scalar, option to enable/disable calculation of interstation distances <br> ***aoi:*** Numeric vector of length four, bounding coordinates of the area of interest <br> ***verbose:*** Logical value, option to show extended function information | List object with distance maps (list of SpatRaster objects from terra package) and station distance matrix (data.frame) | Niaz <br>Available in `R package (eseis)`, to be translated to Python |
| **Seismic Signal Migration** | | | | | |
| spatial_migrate | Migrate signals of a seismic event through a grid of locations | ***data:*** Numeric matrix or eseis object, seismic signals to cross-correlate <br> ***d_stations:*** Numeric matrix, inter-station distances. Output of spatial_distance <br> ***d_map:*** List object, distance maps for each station. Output of spatial_distance <br> ***snr:*** Numeric vector, optional signal-to-noise-ratios for each signal trace, used for normalisation <br> ***v:*** Numeric value, mean velocity of seismic waves (m/s) <br> ***dt:*** Numeric value, sampling period <br> ***normalise:*** Logical value, option to normalise stations correlations by signal-to-noise-ratios <br> ***verbose:*** Logical value, option to show extended function information | SpatialGridDataFrame-object with Gaussian probability density function values for each grid cell | Niaz <br>Available in `R package (eseis)`, to be translated to Python|
| **Seismic Event Localization** | | | | | |
| spatial_amplitude | Locate the source of a seismic event by modelling amplitude attenuation | ***data:*** Numeric matrix or eseis object, seismic signals to work with <br> ***coupling:*** Numeric vector, coupling efficiency factors for each seismic station <br> ***d_map:*** List object, distance maps for each station. Output of spatial_distance <br> ***aoi:*** raster object that defines which pixels are used to locate the source <br> ***v:*** Numeric value, mean velocity of seismic waves (m/s) <br> ***q:*** Numeric value, quality factor of the ground <br> ***f:*** Numeric value, frequency for which to model the attenuation <br> ***a_0:*** Logical value, start parameter of the source amplitude <br> ***normalise:*** Logical value, option to normalise sum of residuals between 0 and 1 <br> ***output:*** Character value, type of metric the function returns <br> ***cpu:*** Numeric value, fraction of CPUs to use |  Raster object with the location output metrics for each grid cell | Niaz <br>Available in `R package (eseis)`, to be translated to Python |
| **Spatial Data Processing** | | | | | |
| spatial_clip | Clip values of spatial data | ***data:*** SpatRaster object, spatial data set to be processed <br> ***quantile:*** Numeric value, quantile value below which raster values are clipped <br> ***replace:*** Numeric value, replacement value <br> ***normalise:*** Logical value, optionally normalise values above threshold quantile between 0 and 1 | SpatRaster object, data set with clipped values | Lamia <br>Available in `R package (eseis)`, to be translated to Python |
| **Coordinate System Conversion** | | | | | |
| spatial_convert | Convert coordinates between reference systems | ***data:*** Numeric vector of length two or data frame, x-, y-coordinates to be converted <br> ***from:*** Character value, proj4 string of the input reference system <br> ***to:*** Character value, proj4 string of the output reference system | Numeric data frame with converted coordinates | Lamia <br>Available in `R package (eseis)`, to be translated to Python |
| **Source Location Determination** | | | | | |
| spatial_pmax | Get most likely source location | ***data:*** SpatRaster object, spatial data set with source location estimates | data.frame, coordinates (x and y) of the most likely source location(s) | Lamia <br>Available in `R package (eseis)`, to be translated to Python |
| **Seismic Source Tracking** | | | | | |
| spatial_track | Track a spatially mobile seismic source |  |  |  |
| **Modelling** | | | | | |
| model_bedload | Model the seismic spectrum due to bedload transport in rivers |  |  |  |
| model_turbulence | Model the seismic spectrum due to hydraulic turbulence |  |  |  |

## Non-Functional Requirements
1. **Performance**
   - The package should handle large datasets efficiently.
   - The processes should be optimized for speed.
2. **Usability**
   - The package should have a clear and concise documentation.
   - The tool should be user-friendly.
3. **Scalability**
   - The package should be able to scale with increasing data sizes and complexity of analyses.
4. **Reliability**
   - The package should provide accurate and consistent results.
   - It should include error handling and logging mechanisms.
5. **Maintainability**
   - The code should follow best practices and be well-documented.
   - The package should be modular to facilitate updates and maintenance.
6. **Compatibility**
   - The package should be compatible with major operating systems (Windows, macOS, Linux).
   - It should support integration with other scientific Python libraries (e.g., NumPy, SciPy, Matplotlib).
---