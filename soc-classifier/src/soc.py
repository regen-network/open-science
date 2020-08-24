import os
from osgeo import gdal
from osgeo import ogr
import numpy as np
import osr
from sklearn.ensemble import RandomForestClassifier
import matplotlib.pyplot as plt
from sklearn import metrics

def create_mask_from_vector(vector_data_path, cols, rows, geo_transform,
                            projection, target_value=1):
    """Rasterize the given vector (wrapper for osgeo.gdal.RasterizeLayer)."""
    data_source = osgeo.gdal.OpenEx(vector_data_path, osgeo.gdal.OF_VECTOR)
    layer = data_source.GetLayer(0)
    driver = osgeo.gdal.GetDriverByName('MEM')  # In memory dataset
    target_ds = driver.Create('', cols, rows, 1, osgeo.gdal.GDT_UInt16)
    target_ds.SetGeoTransform(geo_transform)
    target_ds.SetProjection(projection)
    osgeo.gdal.RasterizeLayer(target_ds, [1], layer, burn_values=[target_value])
    return target_ds


def vectors_to_raster(file_paths, rows, cols, geo_transform, projection):
    """Rasterize the vectors in the given directory in a single image."""
    labeled_pixels = np.zeros((rows, cols))
    print
    for i, path in enumerate(file_paths):
        label = i+1
        ds = create_mask_from_vector(path, cols, rows, geo_transform,
                                     projection, target_value=label)
        band = ds.GetRasterBand(1)
        labeled_pixels += band.ReadAsArray()
        ds = None
    return labeled_pixels


def write_geotiff(fname, data, geo_transform, projection):
    """Create a GeoTIFF file with the given data."""
    driver = osgeo.gdal.GetDriverByName('GTiff')
    rows, cols = data.shape
    dataset = driver.Create(fname, cols, rows, 1, osgeo.gdal.GDT_Byte)
    dataset.SetGeoTransform(geo_transform)
    dataset.SetProjection(projection)
    band = dataset.GetRasterBand(1)
    band.WriteArray(data)
    dataset = None  # Close the file


# Set raster metadata for rasterizing our training data.
bands, rows, cols = arr.shape
geo_transform = [374566.1760405825, 60.0, 0.0, -4276862.181956149, 0.0, -60.0]
proj = 'PROJCS["WGS 84 / UTM zone 60N", GEOGCS["WGS 84", DATUM["WGS_1984", SPHEROID["WGS 84",6378137,298.257223563, AUTHORITY["EPSG","7030"]], AUTHORITY["EPSG","6326"]], PRIMEM["Greenwich",0, AUTHORITY["EPSG","8901"]], UNIT["degree",0.0174532925199433, AUTHORITY["EPSG","9122"]], AUTHORITY["EPSG","4326"]], PROJECTION["Transverse_Mercator"], PARAMETER["latitude_of_origin",0],PARAMETER["central_meridian",177],PARAMETER["scale_factor",0.9996],PARAMETER["false_easting",500000],PARAMETER["false_northing",0], UNIT["metre",1, AUTHORITY["EPSG","9001"]], AXIS["Easting",EAST], AXIS["Northing",NORTH], AUTHORITY["EPSG","32660"]]'


# Stack the bands of the data to prepare for classification
stacked = np.dstack((arr[0],arr[1],arr[2]))

# paths for training and testing data
train_data_path = "data/train/"
validation_data_path = "data/test/"

# read in classes from shapefile
files = [f for f in os.listdir(train_data_path) if f.endswith('.shp')]
classes = [f.split('.')[0] for f in files]
print("There are {} classes:".format(len(classes)))
for c in classes:
    print(c)

shapefiles = [os.path.join(train_data_path, f)
              for f in files if f.endswith('.shp')]

labeled_pixels = vectors_to_raster(shapefiles, rows, cols, geo_transform,
                                   proj)
is_train = np.nonzero(labeled_pixels)
training_labels = labeled_pixels[is_train]
training_samples = stacked[is_train]

# build classifier
classifier = RandomForestClassifier(n_jobs=-1)
classifier.fit(training_samples, training_labels)

# Accuracy assesment
shapefiles = [os.path.join(validation_data_path, "%s.shp"%c) for c in classes]
verification_pixels = vectors_to_raster(shapefiles, rows, cols, geo_transform, proj)
for_verification = np.nonzero(verification_pixels)
verification_labels = verification_pixels[for_verification]
predicted_labels = classification[for_verification]

# confusion matrix
print("Confusion matrix:\n\n{}".format(metrics.confusion_matrix(verification_labels, predicted_labels)))

# accuracy
target_names = ['Class {}'.format(s) for s in classes]
print("Classification report:\n\n {}".format(metrics.classification_report(verification_labels, predicted_labels,
                                    target_names=target_names)))
print("Classification accuracy: {}".format(metrics.accuracy_score(verification_labels, predicted_labels)))


# Should we keep as is or read use the QGIS point sampling tool to extract raster values and build a nd array
