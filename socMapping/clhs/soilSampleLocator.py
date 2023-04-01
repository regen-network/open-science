#!/usr/bin/env python
# coding: utf-8

# In[1]:


# This script is used to calculate an input feature image for the 
# clhsPlotLocation.R R script that calculates soil sample locations 
# based on a conditioned latin hypercube sampling (cLHS) algorithm. 

# This script was written by Ned Horning [ned.horning@regen.network]

# This script is free software; you can redistribute it and/or modify it under the
# terms of the Apache License 2.0 License.  


# In[2]:


import ee
import geemap
import os
from geemap import geojson_to_ee, ee_to_geojson
import geopandas as gpd 
import pandas as pd
import math
import numpy as np

#ee.Authenticate()
ee.Initialize()


# In[3]:


### Enter start and end date as numbers for year, month, day to calculate max NDVI ###
startDate = ee.Date.fromYMD(2021, 1, 1)
endDate = ee.Date.fromYMD(2021, 12, 31)

# Enter the number of samples to place in the area
numSamples = 30

# Scale (resolution) in meters for the analysis
pixScale = 20

# Cloud masking parameters - for more information about the workflow and avriables see:
# https://developers.google.com/earth-engine/tutorials/community/sentinel-2-s2cloudless
cloudFilter = 60
cloudProbabilityThreshold = 50
nirDarkThreshold = 0.15
cloudPProjectedDistance = 1
buffer = 50


# In[4]:


### Enter input and output file paths and names ###
boundaryShp = "/home/nedhorning/RegenNetwork/Soils/Gunningham/Grazing Area Maps/MergedProperties.shp"
outImage = "/home/nedhorning/RegenNetwork/Soils/Gunningham/MergedPropertiesTest.tif"


# In[5]:


# Function to get image data and apply cloud/shadow filter
def get_s2_sr_cld_col(aoi, start_date, end_date):
    # Import and filter S2 SR.
    s2_sr_col = (ee.ImageCollection('COPERNICUS/S2_SR')
        .filterBounds(aoi)
        #.filterMetadata('MGRS_TILE', 'equals', '14SKJ')  # Use this to specify a specific tile
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lte('CLOUDY_PIXEL_PERCENTAGE', cloudFilter)))

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
    is_cloud = cld_prb.gt(cloudProbabilityThreshold).rename('clouds')

    # Add the cloud probability layer and cloud mask as image bands.
    return img.addBands(ee.Image([cld_prb, is_cloud]))


# In[7]:


def add_shadow_bands(img):
    # Identify water pixels from the SCL band.
    not_water = img.select('SCL').neq(6)

    # Identify dark NIR pixels that are not water (potential cloud shadow pixels).
    SR_BAND_SCALE = 1e4
    dark_pixels = img.select('B8').lt(nirDarkThreshold*SR_BAND_SCALE).multiply(not_water).rename('dark_pixels')

    # Determine the direction to project cloud shadow from clouds (assumes UTM projection).
    shadow_azimuth = ee.Number(90).subtract(ee.Number(img.get('MEAN_SOLAR_AZIMUTH_ANGLE')));

    # Project shadows from clouds for the distance specified by the CLD_PRJ_DIST input.
    cld_proj = (img.select('clouds').directionalDistanceTransform(shadow_azimuth, cloudPProjectedDistance *10)
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
    is_cld_shdw = (is_cld_shdw.focal_min(2).focal_max(buffer*2/20)
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


# Need to add cloud removal
def addNDVI(image):
  return image.addBands(image.normalizedDifference(['B8', 'B4']).rename('NDVI'))


# In[11]:


def addTWI(image):
    return image.addBands(TWI.rename('TWI'))


# In[12]:


def addChili(image):
    return image.addBands(chili.rename('CHILI'))


# In[13]:


def addSlope(image):
    return image.addBands(slope.rename('Slope'))


# In[14]:


# Function make the server-side feature collection accessible to the client
def getValues(fc):
    features = fc.getInfo()['features']
    dictarr = []
    for f in features:
        attr = f['properties']
        dictarr.append(attr)
    return dictarr


# In[15]:


# Convert input boundary Shapefile to a GEE boundary feature to constrain spatial extent
boundary_ee = geemap.shp_to_ee(boundaryShp)


# In[16]:


# Get image data using temporal and spatial constraints
s2_sr_cld_col = get_s2_sr_cld_col(boundary_ee, startDate, endDate)


# In[17]:


# Apply cloud/shadow mask and add NDVI layer
sentinelCollection = (s2_sr_cld_col.map(add_cld_shdw_mask)
                             .map(apply_cld_shdw_mask)
                             .map(addNDVI))


# In[18]:


# For each pixel calculate the "greenest" (highest) NDVI value for the entire year
greenest = sentinelCollection.qualityMosaic('NDVI')


# In[19]:


# Image display parameters
sentinel_vis = {
    'min': 0,
    'max': 2500,
    'gamma': [1.1],
    'bands': ['B4', 'B3', 'B2']}


# In[20]:


ndviViz = {'min': -0.5, 
           'max':0.9, 
           'bands': ['NDVI'],
           'palette': ['FFFFFF', 'CE7E45', 'DF923D', 'F1B555', 'FCD163', \
                                               '99B718', '74A901', '66A000', '529400', '3E8601', \
                                               '207401', '056201', '004C00', '023B01', '012E01', \
                                               '011D01', '011301']}


# In[21]:


# Calculate Topographic wetness index and extract points
upslopeArea = (ee.Image("MERIT/Hydro/v1_0_1")
    .select('upa'))
elv = (ee.Image("MERIT/Hydro/v1_0_1")
    .select('elv'))

slope = ee.Terrain.slope(elv)
upslopeArea = upslopeArea.multiply(1000000).rename('UpslopeArea')
slopeRad = slope.divide(180).multiply(math.pi)
TWI = ee.Image.log(upslopeArea.divide(slopeRad.tan())).rename('TWI')


# In[22]:


# Read in and extract points for continuous heat-insolation load index and extract points
chili = (ee.Image("CSP/ERGo/1_0/Global/SRTM_CHILI"))


# In[23]:


dem = ee.Image('NASA/NASADEM_HGT/001').select('elevation')
slope = ee.Terrain.slope(dem)


# In[24]:


predictorImage = addTWI(greenest.select('NDVI'))
predictorImage2 = addChili(predictorImage)
predictorImage3 = addSlope(predictorImage2)


# In[25]:


Map=geemap.Map()
Map.centerObject(boundary_ee, 13)
Map.addLayer(predictorImage3, ndviViz)
Map.addLayer(boundary_ee, {}, "Boundary EE")
Map


# In[26]:


image = predictorImage3.clip(boundary_ee.geometry()).unmask()
geemap.ee_export_image(
    image, filename=outImage, scale=pixScale, region=boundary_ee.geometry(), file_per_band=False
)


# In[ ]:




