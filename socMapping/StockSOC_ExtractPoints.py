#!/usr/bin/env python
# coding: utf-8

# In[1]:


# This script is used to extract Sentinel image data and other layers for a set of 
# soil sample point locations. The DN values for each of the image bands and other 
# layers is output as a dictionary of tabular data that can be processed using the 
# "StockSOC_ProcessPoints" script. Input files are ESRI Shapefiles with the project 
# boundary polygon and the soil sample points locations.A Python pickle file is 
# exported to be input into the "StockSOC_ProcessPoints" script.

# This script was written by Ned Horning [ned.horning@regen.network]

# This script is free software; you can redistribute it and/or modify it under the
# terms of the Apache License 2.0 License.  


# In[2]:


import ee
import geemap
import json
import os
import requests
from datetime import datetime
from geemap import geojson_to_ee, ee_to_geojson
import geopandas as gpd 
import pandas as pd
import pickle
import math

ee.Initialize()


# In[3]:


### Enter start and end date as numbers for year, month, day ###
startDate = ee.Date.fromYMD(2021, 1, 1)
endDate = ee.Date.fromYMD(2021, 12, 31)
# Enter the seasonal portion for each year in the date range to process
startMonth = 1  
endMonth = 12

# Scale (resolution) in meters for the analysis
pixScale = 20

# Cloud masking parameters - for more information about the workflow and avriables see:
# https://developers.google.com/earth-engine/tutorials/community/sentinel-2-s2cloudless
CLOUD_FILTER = 60
CLOUD_PROBABILITY_THRESHOLD = 50
NIR_DARK_THRESHOLD = 0.15
CLOUD_PROJECTED_DISTANCE = 1
BUFFER = 50


# In[4]:


### Enter input and output file paths and names ###
boundaryShp = ""
inPoints = ""
outPickle = ""


# In[5]:


# Function to get image data and apply cloud/shadow filter
def get_s2_sr_cld_col(aoi, start_date, end_date):
    # Import and filter S2 SR.
    s2_sr_col = (ee.ImageCollection('COPERNICUS/S2_SR')
        .filterBounds(aoi)
        #.filterMetadata('MGRS_TILE', 'equals', '14SKJ')  # Use this to specify a specific tile
        .filterDate(start_date, end_date)
        .filter(ee.Filter.calendarRange(startMonth, endMonth,'month'))
        .filter(ee.Filter.lte('CLOUDY_PIXEL_PERCENTAGE', CLOUD_FILTER)))

    # Import and filter s2cloudless.
    s2_cloudless_col = (ee.ImageCollection('COPERNICUS/S2_CLOUD_PROBABILITY')
        .filterBounds(aoi)
        .filterDate(start_date, end_date))

    # Join the filtered s2cloudless collection to the SR collection by the 'system:index' property.
    return ee.ImageCollection(ee.Join.saveFirst('s2cloudless').apply(**{
        'primary': s2_sr_col,
        'secondary': s2_cloudless_col,
        'condition': ee.Filter.equals(**{
            'leftField': 'system:index',
            'rightField': 'system:index'
        })
    }))


# In[6]:


# Cloud cover function

def add_cloud_bands(img):
    # Get s2cloudless image, subset the probability band.
    cld_prb = ee.Image(img.get('s2cloudless')).select('probability')

    # Condition s2cloudless by the probability threshold value.
    is_cloud = cld_prb.gt(CLOUD_PROBABILITY_THRESHOLD).rename('clouds')

    # Add the cloud probability layer and cloud mask as image bands.
    return img.addBands(ee.Image([cld_prb, is_cloud]))


# In[7]:


def add_shadow_bands(img):
    # Identify water pixels from the SCL band.
    not_water = img.select('SCL').neq(6)

    # Identify dark NIR pixels that are not water (potential cloud shadow pixels).
    SR_BAND_SCALE = 1e4
    dark_pixels = img.select('B8').lt(NIR_DARK_THRESHOLD*SR_BAND_SCALE).multiply(not_water).rename('dark_pixels')

    # Determine the direction to project cloud shadow from clouds (assumes UTM projection).
    shadow_azimuth = ee.Number(90).subtract(ee.Number(img.get('MEAN_SOLAR_AZIMUTH_ANGLE')));

    # Project shadows from clouds for the distance specified by the CLD_PRJ_DIST input.
    cld_proj = (img.select('clouds').directionalDistanceTransform(shadow_azimuth, CLOUD_PROJECTED_DISTANCE *10)
        .reproject(**{'crs': img.select(0).projection(), 'scale': 100})
        .select('distance')
        .mask()
        .rename('cloud_transform'))

    # Identify the intersection of dark pixels with cloud shadow projection.
    shadows = cld_proj.multiply(dark_pixels).rename('shadows')

    # Add dark pixels, cloud projection, and identified shadows as image bands.
    return img.addBands(ee.Image([dark_pixels, cld_proj, shadows]))


# In[8]:


def add_cld_shdw_mask(img):
    # Add cloud component bands.
    img_cloud = add_cloud_bands(img)

    # Add cloud shadow component bands.
    img_cloud_shadow = add_shadow_bands(img_cloud)

    # Combine cloud and shadow mask, set cloud and shadow as value 1, else 0.
    is_cld_shdw = img_cloud_shadow.select('clouds').add(img_cloud_shadow.select('shadows')).gt(0)

    # Remove small cloud-shadow patches and dilate remaining pixels by BUFFER input.
    # 20 m scale is for speed, and assumes clouds don't require 10 m precision.
    is_cld_shdw = (is_cld_shdw.focal_min(2).focal_max(BUFFER*2/20)
        .reproject(**{'crs': img.select([0]).projection(), 'scale': 20})
        .rename('cloudmask'))

    # Add the final cloud-shadow mask to the image.
    return img_cloud_shadow.addBands(is_cld_shdw)


# In[9]:


def apply_cld_shdw_mask(img):
    # Subset the cloudmask band and invert it so clouds/shadow are 0, else 1.
    not_cld_shdw = img.select('cloudmask').Not()

    # Subset reflectance bands and update their masks, return the result.
    return img.select('B.*').updateMask(not_cld_shdw)


# In[10]:


# Function make the server-side feature collection accessible to the client
def getValues(fc):
    features = fc.getInfo()['features']
    dictarr = []
    for f in features:
        attr = f['properties']
        dictarr.append(attr)
    return dictarr


# In[11]:


# Convert input boundary Shapefile to a GEE boundary feature to constrain spatial extent
boundary_ee = geemap.shp_to_ee(boundaryShp)


# In[12]:


# Get image data using temporal and spatial constraints
s2_sr_cld_col = get_s2_sr_cld_col(boundary_ee, startDate, endDate)


# In[13]:


# Apply cloud/shadow mask
sentinelCollection = (s2_sr_cld_col.map(add_cld_shdw_mask)
                             .map(apply_cld_shdw_mask))


# In[14]:


# Create a list of dates for all images in the collection
datesObject = sentinelCollection.aggregate_array("system:time_start")
dateList =  datesObject.getInfo()
dateList=[datetime.fromtimestamp(x/1000).strftime('%Y_%m_%d') for x in dateList]


# In[15]:


# Image display parameters
sentinel_vis = {
    'min': 0,
    'max': 2500,
    'gamma': [1.1],
    'bands': ['B4', 'B3', 'B2']}


# In[16]:


# Convert input sample points Shapefile to a GEE feature
sample_locations = geemap.shp_to_ee(inPoints)


# In[17]:


# Dictionary to store all points
extractedValues = {}


# In[18]:


# Calculate Topographic wetness index and extract points
upslopeArea = (ee.Image("MERIT/Hydro/v1_0_1")
    .select('upa'))
elv = (ee.Image("MERIT/Hydro/v1_0_1")
    .select('elv'))

slope = ee.Terrain.slope(elv)
upslopeArea = upslopeArea.multiply(1000000).rename('UpslopeArea')
slopeRad = slope.divide(180).multiply(math.pi)
TWI = ee.Image.log(upslopeArea.divide(slopeRad.tan())).rename('TWI')
extractedPointsTWI = geemap.extract_values_to_points(sample_locations, TWI, scale=pixScale)
dictarrTWI = getValues(extractedPointsTWI)


# In[19]:


# Read in and extract points for continuous heat-insolation load index and extract points
chili = (ee.Image("CSP/ERGo/1_0/Global/SRTM_CHILI"))
extractedPointsCHILI = geemap.extract_values_to_points(sample_locations, chili, scale=pixScale)
dictarrCHILI = getValues(extractedPointsCHILI)


# In[20]:


# Create a list of the images for processing
images = sentinelCollection.toList(sentinelCollection.size())


# In[21]:


Map=geemap.Map()
Map.centerObject(boundary_ee, 13)
for index in range(0, sentinelCollection.size().getInfo()-1):
    print("Processing " + dateList[index] + ": " + str(sentinelCollection.size().getInfo()-1 - index - 1) + " images to go      ", end = "\r")
    image = ee.Image(images.get(index))
    extractedPoints = geemap.extract_values_to_points(sample_locations, image, scale=pixScale)
    dictarr = getValues(extractedPoints)
    points = gpd.GeoDataFrame(dictarr)
    # Add the following variables to the collection of point data
    points['stock'] = points['BD'] * points['C%']
    points['twi'] = gpd.GeoDataFrame(dictarrTWI)['first']
    points['chili'] = gpd.GeoDataFrame(dictarrCHILI)['first']
    
    # Use band 3 to select only points not covered by clouds
    if ('B3' in points):  
        extractedValues.update({dateList[index] : points})
    # Add the image layer for display
    Map.addLayer(image, sentinel_vis, dateList[index])

# Add boundary to dispay images
Map.addLayer(boundary_ee, {}, "Boundary EE")

# Display the map.
Map


# In[22]:


# Output the dictionary with all points - this will be input to the "StockSOC_ProcessPoints" Notebook
with open(outPickle, 'wb') as handle:
    pickle.dump(extractedValues, handle, protocol=pickle.HIGHEST_PROTOCOL)


# In[23]:


# Print a list of all the image dates
list(extractedValues.keys())


# In[24]:


# Print all of the points starting with the earliest date
extractedValues


# In[ ]:




