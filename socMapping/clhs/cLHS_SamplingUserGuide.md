# cLHS Sampling User Guide

Using R and Google Earth Engine to calculate sample points locations using a conditioned latin hypercube sampling (cLHS) algorithm.

## Introduction

This guide explains how to use a workflow to create an ESRI point Shapefile with sample locations distributed across a grazing area that will be modeled to estimate soil organic carbon stocks using satellite imagery.
The workflow is divided into two discrete steps:

- **Step 1**: Running a Jupyter notebook Python script (`soilSampleLocator.ipynb`) that executes an image processing pipeline in Google Earth Engine to create a feature image.

- **Step 2**: Running an R script (`clhsPlotLocation.R`) to calculate sample locations using a conditioned latin hypercube sampling (cLHS) algorithm and the feature image.

## Workflow setup

This workflow requires the following:

1. Google Earth Engine (GEE) account
2. Jupyter Notebook
3. Python 3 with geemap and other Python libraries
4. R with the following libraries: clhs, raster, rgdal, rgeos

### Setup GEE

To use GEE you first need to setup an account.
To do that visit <https://signup.earthengine.google.com/> and fill out the application.
Approval can take some time.

### Install Jupyter Notebook

Next, you will need to install Jupyter Notebook.
Go to the Jupyter Notebook website (<https://jupyter.org/>) and follow the instructions for your operating system.

### Install Python 3 with geemap and other Python libraries

To set up a Python environment and required libraries for running the scripts I suggest you follow the instructions on the geemap website: <https://geemap.org/>.
Following the instructions on the “Installation” page provide guidance on setting up a Python environment to run geemap.

Please note that at the time of writing the instructions require installing python 3.9.
Qiusheng Wu also has several dozen videos about different aspects of geemap and his first tutorial is an excellent supplement to the written instructions for setting up geemap: <https://www.youtube.com/watch?v=h0pz3S6Tvx0&t=31s>.

Depending on which method you use to install Python and geemap you will also need to install specific packages.
When you run one of the Jupyter Notebook scripts you might get an error “No module named” at the beginning of the script.
If that happen you will need to install that Python module (library).
You can use “pip install” as noted in the geemap “Installation” instructions to install missing python modules.

## Running the Jupyter `soilSampleLocator.ipynb` script

Once you have downloaded the Jupyter Notebook scripts to your computer you can start Jupyter Notebook.
If you followed the instructions on the geemap website you can launch Jupyter Notebook using a command terminal.
You can use the following two commands to set the conda environment and then to launch Jupyter Notebook:

```
conda activate gee
jupyter notebook
```

Jupyter Notebook will open a web page that will allow you to navigate to the `soilSampleLocator.ipynb` script.
Clicking on the script will open it in Jupyter Notebook.
The script has a brief overview explaining what the script does and that is followed by a series of import statements to provide access to the different modules the script will need for processing.

Next, there are a few blocks with the first line starting and ending with `###`.
These are blocks where you can define variables for running the scripts.
After editing the variables the entire script can be run by selecting "Kernel" => "Restart & Run All".
The script can also be run one block at a time using the “Run” button at the top of the Jupyter Notebook page under the menu.

## Understanding the `soilSampleLocator.ipynb` script

This script is used to calculate an input feature image for the `clhsPlotLocation.R` R script that calculates soil sample locations based on a conditioned latin hypercube sampling (cLHS) algorithm.
The output from the script is a four-band feature image, defined by the `outImage` variable, with the following values:

- Normalized Difference Vegetation Index (NDVI)
- Topographic Wetness Index (TWI)
- Continuous Heat-Insolation Load Index (CHILI)
- Topographic Slope (Slope)

The NDVI image is calculated using a temporal stack of images that cover the study area which is defined by the `boundaryShp` variable.
The range of dates to include in the image stack are defined by the `startDate` and `endDate` variables.
From that temporal stack, for each pixel, the highest NDVI value through time is used for the output NDVI image band.

The TWI is calculated in the script and the CHILI and Slope images are Google Earth Engine assets.

## Understanding the `clhsPlotLocation.R` R script

The `clhsPlotLocation.R` script takes as input the image that was output from the `soilSampleLocator.ipynb` script described above.
This image is defined by the `inImage` variable.
The input boundary file must also be entered using the `inBoundaryFile` varialbe.

Other input variables include the output ESRI shapefile name which is defined by the `outShapefile` variable name and the number of samples that should be distributed in the area defined by the boundary file.
The number of samples is defined by the `numSamples` variable.

The `bandNames` variable should be set to `c("NDVI", "TWI", "CHILI", "Slope")` if using the feature image output from the `clhsPlotLocation.R` script.
The script can take a minute or so to run and it outputs an ESRI point Shapefile that can be used to locate soil samples in the field.
A plot of the plot locations is also displayed.

## Citation information

If you cite this document we ask that you include the following information:

- Horning, N. 2023. Using R and Google Earth Engine to calculate sample points locations using a conditioned latin hypercube sampling (cLHS) algorithm. Regen Network Development Inc. Available from https://github.com/regen-network/open-science/socMapping. (accessed on the date).
