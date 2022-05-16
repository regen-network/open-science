#!/usr/bin/env python
# coding: utf-8

# In[1]:


# This script is used to process the data output form the “StockSOC_ExtractPoints” script. 
# For each date where point data could be extracted from Sentinel imagery this script will 
# determine the features (variables) that produce a linear regression with the best R2 value. 
# You can specify the minimum and maximum number of features that are tested. Increasing the 
# maximum number of features to four or higher requires significantly more processing time. Using 
# leave-one-out cross validation with the best linear model, the following metrics 
# are calculated and writen to a CSV file that is output at the end of the script: 
# R square, Adjusted R square, RMSE, and normalized RMSE. Processing progress can be monitored 
# by viewing the metrics for each date after that date has been processed.

# This script was written by Ned Horning [ned.horning@regen.network]

# This script is free software; you can redistribute it and/or modify it under the
# terms of the Apache License 2.0 License.  


# In[2]:


import json
import os
import math
import requests
from datetime import datetime
import geopandas as gpd 
import pandas as pd
import pickle
from sklearn import linear_model
from sklearn.model_selection import LeaveOneOut
from mlxtend.feature_selection import ExhaustiveFeatureSelector as EFS
from sklearn.model_selection import train_test_split
from sklearn.model_selection import cross_val_score
from numpy import sqrt 
from numpy import mean 
from numpy import absolute


# In[3]:


### Enter input file from "StockSOC_ExtractPoints" and output CSV file paths and names ###
inPickle = "/home/nedhorning/RegenNetwork/Soils/Ruuts/LaEmma/GEE_Output/extractedPoints.pickle"
outCSV = "/home/nedhorning/RegenNetwork/Soils/Ruuts/LaEmma/GEE_Output/stock.csv"


# In[4]:


### Define the attribute labels from the input tabular data for SOC, BD, and the point name ###
# The attribute labels are the same as the attribute names in the point location ESRI Shapefile
SOC = 'C%'  # Attribute name for soil carbon metric 
BD = 'BD'   # Attribute name for bulk density
PointLabel = 'MUESTRA'   # Attribute name for point labels


# In[5]:


### Specify the minimum and maximum number of features to use for testing best fit ###
min_feat=2
max_feat=3


# In[6]:


### Process stock. To process SOC change to False ###
processStock = True


# In[7]:


# Function to calcualte normalized difference vegetation index
def calcNDVI(red, nir):
    return pd.DataFrame((nir - red)/(nir + red))


# In[8]:


# Function to calcualte soil-adjusted total vegetation index
def calcSATVI(red, swir1, swir2):
    return pd.DataFrame(((swir1 -red)/(swir1 + red+0.5)) * 1.5 - (swir2/2))


# In[9]:


# Function to calcualte normalized burn ratio 2
def calcNBR2(swir1, swir2):
    return pd.DataFrame((swir1 -swir2)/(swir1 + swir2))


# In[10]:


# Function to calcualte soil organic carbon index
def calcSOCI(blue, green, red):
    return pd.DataFrame(blue/(red * green))


# In[11]:


# Function to calcualte bare soil index
def calcBSI(blue, red, nir, swir1):
    return pd.DataFrame((swir1 + red) -(nir + blue) / (swir1 + red) + (nir + blue))


# In[12]:


# Function to calcualte adjusted R2
def adjust_r2(r2, num_examples, num_features):
    coef = (num_examples - 1) / (num_examples - num_features - 1) 
    return 1 - (1 - r2) * coef


# In[13]:


# Open the tabular data that was output from StockSOC_ExtractPoints
with open(inPickle, 'rb') as f:
    pointsDFs = pickle.load(f)


# In[14]:


# Initialize for tabular data to be output to CSV
regResults = pd.DataFrame(columns = ['Date', 'R2', 'Adjusted_R2', 'RMSE', 'BestFeatures'])


# In[15]:


# Iterate through the dictionary of tabular one date at a time to find the set of variables
# that gievs the lowest R2 value
for iteration, key in enumerate(pointsDFs):
    points = pointsDFs[key]
    if (points['B3'].isna().sum() / len(points.index) < 0.2): # If under 20% of the values are NA (cloud masked)
        print("Processing " + key + ": " + (str(len(pointsDFs.keys())-iteration-1)) + 
              " images to go      ", end = "\r")
        points.dropna(inplace=True)
        points['ndvi']= calcNDVI(points['B4'].astype(float), points['B8'].astype(float))
        points['satvi']= calcSATVI(points['B4'].astype(float), points['B11'].astype(float), 
                                   points['B12'].astype(float))
        points['nbr2']= calcNBR2(points['B11'].astype(float), points['B12'].astype(float))
        points['soci']= calcSOCI(points['B2'].astype(float), points['B3'].astype(float), 
                                 points['B4'].astype(float))
        points['bsi']= calcBSI(points['B2'].astype(float), points['B4'].astype(float), 
                                 points['B8'].astype(float), points['B11'].astype(float))

        x = pd.DataFrame(points.drop([SOC, BD, PointLabel, 'stock'], axis=1))
        if (processStock):
            y = points[['stock']]
        else:
            y = points[[SOC]]
        # Set up for leave one out processig
        # Set up for linear regression model
        regr = linear_model.LinearRegression()
        # Execute exhaustive feature selection algorithm
        efs = EFS(regr, 
            min_features=min_feat,
            max_features=max_feat,
            scoring='r2',
            cv=math.floor(len(points.index)/2))
        efs.fit(x, y)
        # Calculate adjusted R2
        for i in efs.subsets_:
            efs.subsets_[i]['adjusted_avg_score'] = (
            adjust_r2(r2=efs.subsets_[i]['avg_score'],
                  num_examples=x.shape[0]/10,
                  num_features=len(efs.subsets_[i]['feature_idx']))
            )
        score = -99e10
        # Select the best adjusted R2
        for i in efs.subsets_:
            score = efs.subsets_[i]['adjusted_avg_score']
            if ( efs.subsets_[i]['adjusted_avg_score'] == score and
                len(efs.subsets_[i]['feature_idx']) < len(efs.best_idx_) )\
              or efs.subsets_[i]['adjusted_avg_score'] > score:
                efs.best_idx_ = efs.subsets_[i]['feature_idx']

        print('Best subset:', efs.best_feature_names_)
        x = points[list(efs.best_feature_names_)]
        if (processStock):
            y = points[['stock']]
        else:
            y = points[[SOC]]
        
        # Get the R2 Adjusted R2, RMSE and Normalize RMSE for the variable with the best fit
        regr = linear_model.LinearRegression()
        fitTOC = regr.fit(x, y)
        R2TOC = fitTOC.score(x,y)
        Adjusted_R2 = 1 - (1-fitTOC.score(x, y))*(len(y)-1)/(len(y)-x.shape[1]-1)
        
        # Calculate RMSE and Normalized RMSE using leave one out cross validation
        cv = LeaveOneOut()
        scores = cross_val_score(regr, x, y, scoring='neg_mean_squared_error',
                         cv=cv, n_jobs=-1)
        RMSE = sqrt(mean(absolute(scores)))
        NRMSE = RMSE/list(y.mean())[0]
        
        # Print values to monitor processing
        print('R2 score: {:.2f}'.format(R2TOC))
        print('Adjusted R2 score: {:.2f}'.format(Adjusted_R2))
        print('RMSE: {:.2f}'.format(RMSE))
        print('NRMSE: {:.2f}'.format(NRMSE))
        
        # Append results to the table that will be outupt as a CSV file
        regResults = regResults.append({'Date' : key, 'R2' : R2TOC, 'Adjusted_R2' : Adjusted_R2, 
                                        'RMSE' : RMSE, 'NRMSE' : NRMSE, 'BestFeatures' : efs.best_feature_names_}, 
                                       ignore_index = True)


# In[16]:


# Output tabular data to CSV file
regResults.to_csv(outCSV, index=False)

