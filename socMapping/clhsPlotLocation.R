# This script applies a conditioned latin hypercube sampling (cLHS) algorithm 
# to image created using a Jupyter notebook script (soilSampleLocator.ipynb). 
# Note that the image does not need to be scaled since that is done in the 
# cLHS algorithm The image covers the study area and has the following default bands: 
#   Normalized Difference Vegetation Index (NDVI)
#   Topographic Wetness Index (TWI)
#   Continuous Heat-Insolation Load Index (CHILI)
#   Topographic Slope (Slope)
#
# The cLHS algorithm to distributes a user-assigned number of sample points 
# (numSamples) throughout the area. The user also needs to enter the path and 
# file names for the input image file (inImage), output point Shapefile with 
# the sample locations (outShapefile), and study area boundary polygon 
# Shapefile (inBoundaryFile). It’s important that the projections  of the 
# boundary shapefile and image are the same.

# When the script runs the samples are plotted in the Plots window.

# This script is free software; you can redistribute it and/or modify it under the 
# terms of the GNU General Public License as published by the Free Software Foundation
# either version 2 of the Licenase, or ( at your option ) any later version.    
#############################################################################
#Load libraries
library(raster)
library(clhs)
library(rgdal)
library(rgeos)
#############################   SET VARIABLES HERE  ############################
# No-data value for the input image
nd <- 0

inImage <- "/home/nedhorning/RegenNetwork/Soils/Gunningham/Grazing Area Maps/MergedProperties.tif"
outShapefile <- "/home/nedhorning/RegenNetwork/Soils/R_Scripts/Testing/Test.shp"
inBoundaryFile <- "/home/nedhorning/RegenNetwork/Soils/Gunningham/Grazing Area Maps/MergedProperties.shp"
bandNames <- c("NDVI", "TWI", "CHILI", "Slope")
numSamples <- 100
#######################################################################################
# Ensures the output will be the same for subsequent runs with the some input data
set.seed(1) 

shapefileLayerName <- strsplit(tail(unlist(strsplit(inBoundaryFile, "/")), n=1), "\\.")[[1]] [1]
boundary <- readOGR(inBoundaryFile, shapefileLayerName)

image <- stack(inImage)
names(image) <- bandNames
image[image==nd] <- NA

# Clip pixels outside of boundary polygons
image <- mask(image, boundary)

points <- rasterToPoints(image,spatial=TRUE)

samples <- clhs(points, numSamples)
geoSamples <- points[samples,]

shapefile(geoSamples, outShapefile, overwrite=TRUE)
plot(geoSamples)

