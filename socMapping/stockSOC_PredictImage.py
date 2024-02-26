#!/usr/bin/env python
# coding: utf-8

# In[1]:


# This script is used to predict SOC% or stock to create an output image based on linear 
# regression model coefficients calculated from the previous (StockSOC_ProcessPoints) script. 
# The output will be a 16-bit integer GeoTIFF image with pixel units of either SOC 
# stock/hectare or SOC%/hectare. 

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


### Enter Sentinel image date as numbers for year, month, day ###
date = ee.Date.fromYMD(2021, 11, 11) # This is the date of the image you want to process  

# Scale (resolution) in meters for the output image
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
outImage = ""


# In[5]:


### Enter intercept, regression coefficients and image bands to use ###
intercept = -0.0044025
coef = [-6.76970035e-03, 6.17522235e-03, 1.19328667e+01]
bands = ['B7', 'B8A', 'nbr2']


# In[6]:


# Function to get image data and apply cloud/shadow filter
def get_s2_sr_cld_col(aoi, start_date):
    # Import and filter S2 SR.
    s2_sr_col = (ee.ImageCollection('COPERNICUS/S2_SR')
        .filterBounds(aoi)
        #.filterMetadata('MGRS_TILE', 'equals', '14SKJ')  # Use this to specify a specific tile
        .filterDate(start_date, start_date.advance(1, 'day'))
        .filter(ee.Filter.lte('CLOUDY_PIXEL_PERCENTAGE', CLOUD_FILTER)))

    # Import and filter s2cloudless.
    s2_cloudless_col = (ee.ImageCollection('COPERNICUS/S2_CLOUD_PROBABILITY')
        .filterBounds(aoi)
        .filterDate(start_date, start_date.advance(1, 'day')))

    # Join the filtered s2cloudless collection to the SR collection by the 'system:index' property.
    return ee.ImageCollection(ee.Join.saveFirst('s2cloudless').apply(**{
        'primary': s2_sr_col,
        'secondary': s2_cloudless_col,
        'condition': ee.Filter.equals(**{
            'leftField': 'system:index',
            'rightField': 'system:index'
        })
    }))


# In[7]:


# Cloud cover function

def add_cloud_bands(img):
    # Get s2cloudless image, subset the probability band.
    cld_prb = ee.Image(img.get('s2cloudless')).select('probability')

    # Condition s2cloudless by the probability threshold value.
    is_cloud = cld_prb.gt(CLOUD_PROBABILITY_THRESHOLD).rename('clouds')

    # Add the cloud probability layer and cloud mask as image bands.
    return img.addBands(ee.Image([cld_prb, is_cloud]))


# In[8]:


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


# In[9]:


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
# return img.addBands(is_cld_shdw)


# In[10]:


def apply_cld_shdw_mask(img):
    # Subset the cloudmask band and invert it so clouds/shadow are 0, else 1.
    not_cld_shdw = img.select('cloudmask').Not()

    # Subset reflectance bands and update their masks, return the result.
    return img.select('B.*').updateMask(not_cld_shdw)


# In[11]:


# Function make the server-side feature collection accessible to the client
def getValues(fc):
    features = fc.getInfo()['features']
    dictarr = []
    for f in features:
        attr = f['properties']
        dictarr.append(attr)
    return dictarr


# In[12]:


# Convert input boundary Shapefile to a GEE boundary feature to constrain spatial extent
boundary_ee = geemap.shp_to_ee(boundaryShp)


# In[13]:


# Get image data using temporal and spatial constraints
s2_sr_cld_col = get_s2_sr_cld_col(boundary_ee, date)


# In[14]:


# Apply cloud/shadow mask and add NDVI layer
sentinelCollection = (s2_sr_cld_col.map(add_cld_shdw_mask)
                             .map(apply_cld_shdw_mask))


# In[15]:


# Image display parameters
sentinel_vis = {
    'min': 0,
    'max': 2500,
    'gamma': [1.1],
    'bands': ['B4', 'B3', 'B2']}

predViz = {'min': 0, 'max': 4, 'palette': ['FF0000', '00FF00']}


# In[16]:


# Dictionary to store all points
allPoints = {}


# In[17]:


# Calculate Topographic wetness index and extract points
upslopeArea = (ee.Image("MERIT/Hydro/v1_0_1")
    .select('upa'))
elv = (ee.Image("MERIT/Hydro/v1_0_1")
    .select('elv'))

slope = ee.Terrain.slope(elv)
upslopeArea = upslopeArea.multiply(1000000).rename('UpslopeArea')
slopeRad = slope.divide(180).multiply(math.pi)
TWI = ee.Image.log(upslopeArea.divide(slopeRad.tan())).rename('twi')


# In[18]:


# Read in and extract points for continuous heat-insolation load index and extract points
chili = (ee.Image("CSP/ERGo/1_0/Global/SRTM_CHILI"))


# In[19]:


img = sentinelCollection.first().addBands(TWI).addBands(chili.rename('chili'))


# In[20]:


# Calculate NDVI
ndvi = img.expression('(nir - red)/(nir + red)', {
    'red' : img.select('B4'),
    'nir' : img.select('B8')}).rename('ndvi')


# In[21]:


# Calculate SATVI
satvi = img.expression('((swir1 -red)/(swir1 + red+0.5)) * 1.5 - (swir2/2)', {
    'red' : img.select('B4'),
    'swir1' : img.select('B11'),
    'swir2' : img.select('B12')}).rename('satvi')


# In[22]:


# Calculate NBR2
nbr2 = img.expression('(swir1 -swir2)/(swir1 + swir2)', {
    'swir1' : img.select('B11'),
    'swir2' : img.select('B12')}).rename('nbr2')


# In[23]:


# Calculate SOCI
soci = img.expression('blue/(red * green)', {
    'blue' : img.select('B2'),
    'green' : img.select('B3'),
    'red' : img.select('B4')}).rename('soci')


# In[24]:


# Calculate BSI
bsi = img.expression('(swir1 + red) -(nir + blue) / (swir1 + red) + (nir + blue)', {
    'blue' : img.select('B2'),
    'red' : img.select('B4'),
    'nir' : img.select('B8'),
    'swir1' : img.select('B11')}).rename('bsi')


# In[25]:


# Combine all bands into a single image
finalImage = img.addBands(ndvi).addBands(satvi).addBands(nbr2).addBands(soci).addBands(bsi)


# In[26]:


# Select the regression prediction algoritm bases on number of coefficients
if len(coef) == 2 :
    exp = str(intercept) + ' + (' + str(coef[0]) + ' * b1)' + ' + (' + str(coef[1]) + ' * b2)'
    print('Prediction equation: ' + exp)
    predImage = finalImage.expression(exp, {
            'b1' : finalImage.select(bands[0]),
            'b3' : finalImage.select(bands[1])})
elif len(coef) == 3 :
    exp = str(intercept) + ' + (' + str(coef[0]) + ' * b1)' + ' + (' + str(coef[1]) + ' * b2)' + \
    ' + (' + str(coef[2]) + ' * b3)'
    print('Prediction equation: ' + exp)
    predImage = finalImage.expression(exp, {
            'b1' : finalImage.select(bands[0]),
            'b2' : finalImage.select(bands[1]),
            'b3' : finalImage.select(bands[2])})
elif len(coef) == 4 :
    exp = str(intercept) + ' + (' + str(coef[0]) + ' * b1)' + ' + (' + str(coef[1]) + ' * b2)' + \
    ' + (' + str(coef[2]) + ' * b3)' + ' + (' + str(coef[3]) + ' * b4)' 
    print('Prediction equation: ' + exp)
    predImage = finalImage.expression(exp, {
            'b1' : finalImage.select(bands[0]),
            'b2' : finalImage.select(bands[1]),
            'b3' : finalImage.select(bands[2]),
            'b4' : finalImage.select(bands[3])})
else:
    print("The number of regression coeficients must be between 2 and 4")


# In[27]:


Map=geemap.Map()
Map.centerObject(boundary_ee, 13)
Map.addLayer(predImage, predViz, 'pred')
Map.addLayer(boundary_ee, {}, "Boundary EE")
Map


# In[28]:


Map=geemap.Map()
Map.centerObject(boundary_ee, 13)
Map.addLayer(finalImage, sentinel_vis, "image")
Map.addLayer(boundary_ee, {}, "Boundary EE")
Map


# In[29]:


# Multiply the output image by 10 to be able to convert to integer allowing larger areas to be downloaded
outputImage = predImage.multiply(10).round().toInt16()


# In[30]:


geemap.ee_export_image(outputImage, filename=outImage, scale=pixScale, region=boundary_ee.geometry(), \
    file_per_band=True)

