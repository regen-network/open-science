<p align="center">
	<img src="media/rnd_logo.png" width=20%
	height=20%>
</p>

<h1 align="center">
	User Guide
</h1>
<h3 align="center">
	Using Google Earth Engine to Predict Soil Organic Carbon using Soil Sample Data & Sentinel-2 Imagery
</h3>

## Introduction

This guide explains how to use Google Earth Engine to create a predicted
map of soil organic carbon (SOC) across a landscape using soil sample
data. The workflow is implemented in two Python scripts designed for use
in Jupyter Notebook.

The workflow consists of two steps. The first step extracts pixel data
from time series Sentinel-2 imagery and other layers that correspond
with soil sample point locations. The second step uses the extracted
data from the first step to find the variables that provide the best
fitting linear regression model. Variables from the model with the best
fit are then used to calculate metrics using leave-one-out
cross-validation (R square, Adjusted R square, RMSE, and normalized
RMSE) to calculate accuracy of the predictions. This is done for each
date of the time-series Sentinel-2 imagery. Output is a CSV file and
that can be view to find the image date and specific variables that
produce the best SOC predictions.

The Jupyter Notebook scripts are written in Python and rely heavily on
the geemap library maintained by Qiusheng Wu. The scripts were developed
to facilitate processing of SOC soil sample data and are intended to be
improved upon by the community of users. The scripts are written to make
them easy to modify and run but users are encouraged to read through and
understand the processing workflow and provide feedback through the
GitHub Issues feature so we can continually improve the scripts.

## Workflow setup

This workflow requires the following:

-   Google Earth Engine (GEE) account

-   Jupyter Notebook

-   Python 3 with geemap and other Python libraries

### Setup GEE

To use GEE you first need to setup an account. To do that visit
<https://signup.earthengine.google.com/> and fill out the application.
Approval can take some time.

### Install Jupyter Notebook

Next, you will need to install Jupyter Notebook. Go to the Jupyter
Notebook website (<https://jupyter.org/>) and follow the instructions
for your operating system.

### Install Python 3 with geemap and other Python libraries

To set up a Python environment and required libraries for running the
scripts I suggest you follow the instructions on the geemap website:
<https://geemap.org/>. Following the instructions on the "Installation"
page provide guidance on setting up a Python environment to run geemap.
Please note that at the time of writing the instructions require 
installing python 3.9. Qiusheng Wu also has several dozen videos about 
different aspects of geemap and his first tutorial is an excellent 
supplement to the written instructions for setting up geemap:
<https://www.youtube.com/watch?v=h0pz3S6Tvx0&t=31s>.

Depending on which method you use to install Python and geemap you will
also need to install specific packages. When you run one of the Jupyter
Notebook scripts you might get an error "No module named" at the
beginning of the script. If that happen you will need to install that
Python module (library). You can use "pip install" as noted in the
geemap "Installation" instructions to install missing python modules.

## Edit soil sample Shapefile before running the scripts

Before running the scripts you will need to create a point Shapefile with 
all of the soil samples and the attribute information must contain the 
following fields;  soil organic carbon percent, bulk density, and a point 
label. These should be the only fields in the attribute table. If the 
original attribute table has more than these three fields the other 
attributes should be deleted.

## Running the scripts

Once you have downloaded the Jupyter Notebook scripts to your computer
you can start Jupyter Notebook. If you followed the instructions on the
geemap website you can launch Jupyter Notebook using a command terminal.
You can use the following two commands to set the conda environment and
then to launch Jupyter Notebook:

`conda activate gee`

`jupyter notebook`

Jupyter Notebook will open a web page that will allow you to navigate to
the scripts. We will be using these two scripts:
StockSOC_ExtractPoints.ipynb and StockSOC_ProcessPoints.ipynb. Clicking
on a script will open it in Jupyter Notebook. Each scrip has a brief
overview explaining what the script does and that is followed by a
series of import statements to provide access to the different modules
the script will need for processing. Next, there are a few blocks with
the first line starting and ending with "\#\#\#". These are blocks where
you can define variables for running the scripts. After editing the
variables the entire script can be run by selecting Kernel =\> Restart &
Run All. The script can also be run one block at a time using the "Run"
button at the top of the Jupyter Notebook page under the menu.

Each script has a processing message to give you an idea how the
processing is progressing. Extracting points is typically finished in a
few minutes but the processing script can take much longer depending on
the maximum number of variable you permit when calculating best fit.

## Understanding the StockSOC_ExtractPoints.ipynb script

This script is used to extract Sentinel image data and other layers for
a set of soil sample point locations. The DN values for each of the
image bands and other layers is output as a dictionary of tabular data
that can be processed using the \"StockSOC_ProcessPoints\" script. Input
files are two ESRI Shapefiles. One with the project boundary polygon and
the other soil sample points locations. A Python pickle file is exported
to be input into the \"StockSOC_ProcessPoints\" script.

Before running the script there are two sets of dates that need to be
entered. The first set defines the start and end date for the Sentinel-2
image search. The second set is used to define a season (specific
months) for each year within the start and end date. This feature makes
is possible to constrain a search to select, for example, only summer
imagery over a multi-year period. To set the resolution that will be
used when extracting data use the "pixScale" variable. This scale
variable is used by GEE to select the appropriate resolution imagery and
sub-sample appropriately.

There are five variables related to the cloud and cloud-shadow screening
algorithm that is being applied in the script. The default variables in
the script are performing well and we have not experimented much with
different options. The cloud masking algorithm and the variables is
explained here:
<https://developers.google.com/earth-engine/tutorials/community/sentinel-2-s2cloudless>

The last set of variables to be entered are the input and output files.
The two input files are ESRI Shapefiles, one polygon file that specifies
the image area to be extracted and the second is a point file with the
location of each soil sample and the SOC, bulk density, and point label
as attribute information.

In addition to using all of the Sentinel-2 image bands the script also
calculates a topographic wetness index layer and reads in the continuous
heat-insolation load index from the GEE image archive.

For each image date, the soil sample point data is used to extract the
image data under each point using the resolution specified by the
"pixScale" variable. For each date a table with the following variables
will be created: pixel values for each of the Sentinel-2 image bands,
topographic wetness index, continuous heat-insolation load index, sample
bulk density, SOC, carbon stock, and point label.

Tabular data for each date as well as the date of the image is stored in
a Python Dictionary and that is exported as a Python pickle file so it
can be input into the StockSOC_ProcessPoints.ipynb script.

## Understanding the StockSOC_ProcessPoints.ipynb script

This script is used to process data output from the
"StockSOC_ExtractPoints" script. For each date where point data could be
extracted from Sentinel imagery this script will determine the features
(variables) that produce a linear regression with the best R2 value. You
can specify the minimum and maximum number of features that are tested.
Increasing the maximum number of features to four or higher requires
significantly more processing time. Using leave-one-out cross validation
with the best fitting linear model, the following metrics are calculated
and writen to a CSV file that is output at the end of the script: R
square, Adjusted R square, RMSE, and normalized RMSE. Processing
progress can be monitored by viewing the metrics for each date after
that date has been processed.

There are three sets of variables that need to be defnied to run the
script. The first set defines the input pickle file exported by the
StockSOC_ExtractPoints.ipynb script and the output CSV file. The next
set identifies the attribute labels from the input tabular data for soil
organic carbon, bulk density, and the point name. The attribute labels
are identical to the attribute names in the point location ESRI
Shapefile. The last set of variables is used to define the minimum and
maximum number of features to use in the exhaustive feature selection
algorithm. Adding more features will dramatically increase processing
time.

The script calculates several indices that are not included in the the
tabular data exported from the StockSOC_ExtractPoints.ipynb script.
These are:

-   normalized difference vegetation index

-   soil-adjusted total vegetation index

-   normalized burn ratio 2

-   soil organic carbon index

-   bare soil index

The script iterates through the dictionary of tabular, one date at a
time, to find the set of variables that gives the lowest R^2^ value
using the exhaustive feature selection algorithm. Predictions from the
model with the best fit based on R^2^ are then selected to calculate the
following accuracy metrics using leave-one-out cross validation: R^2^,
Adjusted R^2^, RMSE, and normalized RMSE. Also output is information 
about the best fitting regression including the features (bands) used, 
intercept, and regression coefficients. The results for each date are 
output while the script runs in the Jupyter Notebook along with a 
message indication how many images remain to be processed. At the end 
of the script the results from each date are output as a CSV file. The 
CSV file can then be examined to see which date and which set of variables 
provide the highest accuracy SOC map. 

## Creating prediction image using stockSOC_PredictImage.ipynb
To create a SOC% or stock prediction image you need to select the image date 
from the table output when running the StockSOC_ProcessPoints.ipynb script. 
In most cases that will be the date that had the lowest RMSE. At present, 
the number regression coefficients must be between 2 and 4. If a higher 
dimensional regression is required the script can be easily edited to 
accommodate that. 

To run the “stockSOC_PredictImage” script you need to enter the date of 
the Sentinel-2 image that you want to process. The resolution and cloud 
screening variables are the same as those described above for the 
“StockSOC_ExtractPoints” script. In the next code block enter the path 
and filename for the ESRI Shapefiles. with the project boundary polygon 
and the path and filename for the output GeoTIFF image. In the next code 
block you will enter the following data that can be copied from the table 
output from the “StockSOC_ProcessPoints” script: features (bands), 
intercept, and regression coefficients.  The  intercept, and regression 
coefficients variable must be entered as an array with commas separating 
each value. 

When you run the script it can take several seconds to output the image. 
When the script is running you can see the prediction equation that is 
being used to confirm the correct regression coefficients are being used. 
Before the output image is created the predicted image is displayed with 
higher values of SOC or stock appearing green and lower values appearing 
red. A false color image is also displayed so you can verify that the 
area of interest (noted with a shaded polygon) is free of clouds with 
appear as cyan colored blobs. The output image should appear in the path 
specified near the top of the script. The image is a single-band 16-bit 
integer image with SOC or stock values multiplied by 1000. The conversion 
to integer was done to reduce the image size and therefore allow a larger 
area to be processed. Google Earth Engine imposes strict output image 
size constraints so it is possible that large areas will not be output. 
If that happens it will be necessary to subset the area being processed 
by cutting the boundary file into multiple polygons and running each 
polygon separately.  The resulting output images can then be mosaicked 
to view the full study area.

## Citation information

If you cite this document we ask that you include the following
information:

Horning, N. 2022. User Guide - Using Google Earth Engine to Predict Soil
Organic Carbon using Soil Sample Data & Sentinel-2 Imagery. Regen
Network Development Inc. Available from
https://github.com/regen-network/open-science/socMapping. (accessed on
the date).
