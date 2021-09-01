#############################################################################
#
# This script calculates NDVI for fields defined by polygons from a directory 
# of images acquired at different dates and outputs two CSV files with the 
# per-field mean NDVI and normalized mean NDVI for each field. 
#
# The following input variables can be set at the top of the script:
# Working directory: 
#   setwd("/home/nedhorning/RegenNetwork/fiberShed/PlanetScope/KaosTest")
# Distance to shrink each polygon: 
#   shrinkSize = -10
# Path to the directory of images: 
#   pathToImages <- "KaosTest_psscene4band_analytic_sr_udm2/files/"
# Bands for calculating NDVI:
#   nirBand <- 4
#   redBand <- 3
# Regular expression used to select image files
#   regExp <- ".tif"
# Polygon attribute holding the field number identifier, start and end grazing dates
#   fieldNameAttribute <- "OBJECTID"
#   startDateAttribute <- "Start_Date"
#   endDateAttribute <- "End_Date"
# Output PDF plot and CSV table file names:
#   pdfPlotFile <- 'ndviStatsBuf.pdf'
#   pdfAvgPlotFile <- 'ndviStatsAvgBuf.pdf'
#   outCSVFileNDVI <- 'ndviStatsBuf.csv'
#   outCSVFileAvgNDVI <- 'ndviStatsAvgBuf.csv'
#
# This script was written by Ned Horning [ned.horning@regen.network] with funding
# from a California, Natural Resources Conservation Service Conservation Innovation 
# Grant. The work was conducted with collaboration from the Fibershed project. 
#
#############################################################################
#Load libraries
require(maptools)
require(sp)
require(raster)
require (rgdal)
require(rgeos)

cat("Set variables and start processing\n")
#############################   SET VARIABLES HERE  ###################################
# Set working directory
setwd("/home/nedhorning/RegenNetwork/fiberShed/MonitoringResults")
# Name and path for the Shapefile (don't need the .shp extension)
shapefile <- "KaosNorth2020UTM10.shp"
shrinkSize = -10

pathToImages <- "Images/KaosNorth2020_clipped_psscene4band_analytic_sr_udm2/files/"

# Band numbers for the near-infrared and red bands
nirBand <- 4
redBand <- 3

# Regular expression used to select image files
regExp <- ".*?_SR.*?tif$"  # Another option matching multiple sub-strings is: ".*?_SR.*?tif*"

# Polygon attribute holding the field number identifier
fieldNameAttribute <- "OBJECTID"
startDateAttribute <- "Start_Date"
endDateAttribute <- "End_Date"

pdfPlotFile <- 'KaosNorth2020/ndviQuantile.pdf'
pdfAvgPlotFile <- 'KaosNorth2020/normalizedQuantile.pdf'
outCSVFileNDVI <- 'KaosNorth2020/ndviStats.csv'
outCSVFileAvgNDVI <- 'KaosNorth2020/ndviStatsNormalized.csv'
#######################################################################################
# Define NDVI function 
ndviFun <- function(nir, red) {(nir - red)/(nir + red)}

# Function to return lowest NDVI value from NDVI just before and after end of grazing date
wasGrazed <- function(ndviVec, endOfGrazing) {
  quantNDVI50 <- quantile(ndviVec)['50%']
  greaterDates <- uniqueDates[which(uniqueDates > endOfGrazing)]
  nextDate <- greaterDates[which(abs(greaterDates-endOfGrazing) == min(abs(greaterDates-endOfGrazing)))]
  nextDateIndex <- which(uniqueDates == nextDate)
  lesserDates <- uniqueDates[which(uniqueDates < endOfGrazing )]
  prevDate <- lesserDates[which(abs(lesserDates-endOfGrazing) == min(abs(lesserDates-endOfGrazing)))]
  prevDateIndex <- which(uniqueDates == prevDate)
  sameDate <- as.Date(endOfGrazing, "%Y/%m/%d") %in% uniqueDates
  if (sameDate) {lowNDVI = ndviVec[which(uniqueDates == endOfGrazing)]} else {lowNDVI = 999}
  if (ndviVec[nextDateIndex] < lowNDVI ) {lowNDVI = ndviVec[nextDateIndex]}
  if (ndviVec[prevDateIndex] < lowNDVI ) {lowNDVI = ndviVec[prevDateIndex]}
  lowNDVI < quantNDVI50
}

# Read the Shapefile
shapefileLayerName <- strsplit(tail(unlist(strsplit(shapefile, "/")), n=1), "\\.")[[1]] [1]
vec <- readOGR(shapefile, shapefileLayerName)
fieldAttributes <- vec[[fieldNameAttribute]]
startDates<- vec[[startDateAttribute]]
startDates <- substr(startDates,1, 10)
endDates <- vec[[endDateAttribute]]
endDates <- substr(endDates,1, 10)

# Shrink polygons 
vecBuf <- gBuffer(vec, byid= TRUE, width=shrinkSize)

grazingDates <- paste(startDates, "-", endDates)
endDates <- as.Date(endDates, "%Y/%m/%d")
startDates <- as.Date(startDates, "%Y/%m/%d")

# Create vector of satellite imaeg file names 
imageList <- list.files(pathToImages, pattern=regExp)
#imageList <- list.files(pathToImages, pattern=".*?_SR.*?tif*")

# 
# Extract date from file name
allDates <- as.Date(substr(imageList,1, 8),  "%Y%m%d")
uniqueDates <- allDates[!duplicated(allDates)]
datesToMosaic <- allDates[duplicated(allDates)]
imagesMinusDuplicares <- imageList[!duplicated(allDates)]

cat("Creating NDVI stack\n")
# Initialize NDVI stack
ndvi <- stack()
# Make stack of NDVI images and mosaic when necessary
for (i in 1:length(uniqueDates)) {
  if (uniqueDates[i] %in% datesToMosaic) {
    datesToMosaic <- datesToMosaic[which(datesToMosaic!=uniqueDates[i])]
    imagesToMosaic <- imageList[allDates==uniqueDates[i]]
    brickList <- list()
    for (j in 1:length(imagesToMosaic)) {
      brickList <- append(brickList, brick(paste(pathToImages, imagesToMosaic[j], sep='')))
    }
    image <- do.call(merge, brickList)
  } else {
    image <- brick(paste(pathToImages, imagesMinusDuplicares[i], sep=''))
  }
  
  ndvi <- addLayer(ndvi, overlay(image[[nirBand]], image[[redBand]], fun=ndviFun))
  # writeRaster(ndvi[[i]], paste("ndvi_", uniqueDates[i], ".tif", sep=""))
}

cat("Extract NDVI values and calculate means\n")
# Extract NDVI values and calculate the mean from each polygon
statsNDVI <- extract(ndvi, vecBuf, fun=mean)
# Use original vector file to get the object ids for each polygon
rownames(statsNDVI) <- fieldAttributes
colnames(statsNDVI) <- as.character(uniqueDates)
# Create an empty matrix to hold difference from mean NDVI values
statsAvgNDVI <- matrix(nrow=nrow(statsNDVI), ncol=ncol(statsNDVI))
# Use original vector file to get the object ids for each polygon
rownames(statsAvgNDVI) <- fieldAttributes
colnames(statsAvgNDVI) <- as.character(uniqueDates)

# Calculate difference from overall mean NDVI for each polygon
for (c in 1:ncol(statsNDVI)) {
  for (r in 1:nrow(statsNDVI)) {
    statsAvgNDVI[r,c] <- statsNDVI[r,c] - mean(statsNDVI[,c])
  }
}

grazingHappened <- logical(length(endDates))
names(grazingHappened) <- as.character(fieldAttributes)
for (i in 1:length(endDates)) {
  if (!is.na(endDates[i])) {grazingHappened[i]=wasGrazed(statsAvgNDVI[i,], endDates[i])} else {
    grazingHappened[i] = NA
  }
}

pdf(file=pdfPlotFile)
par(mfrow = c(3,2))
for (i in 1:nrow(statsNDVI)) {
  plot(statsNDVI[i,] ~ uniqueDates, ylim = c(0, 1), type='l', xlab="", ylab="")
  title(paste("Plot ", fieldAttributes[i], " (", grazingHappened[i], ")", ": ", grazingDates[i], sep=''))
  grid (NA,NULL, lty = 6, col = "cornsilk2") 
  abline(v=endDates[i], col="Green")
  abline(v=startDates[i], col="Yellow")
}
dev.off()

pdf(file=pdfAvgPlotFile)
par(mfrow = c(3,2))
for (i in 1:nrow(statsAvgNDVI)) {
  plot(statsAvgNDVI[i,] ~ uniqueDates, ylim = c(-0.25, 0.15), type='l', xlab="", ylab="")
  title(paste("Plot ", fieldAttributes[i], " (", grazingHappened[i], ")", ": ", grazingDates[i], sep=''))
  grid (NA,NULL, lty = 6, col = "cornsilk2")
  abline(v=endDates[i], col="Green")
  abline(v=startDates[i], col="Yellow")
}
dev.off()

cat("Output files\n")
# Output CSV files
write.csv(statsNDVI, outCSVFileNDVI)
write.csv(statsAvgNDVI, outCSVFileAvgNDVI)
# Output the reduced polygon file 
# shapefile(vecBuf, "bufferedPoly.shp") 
