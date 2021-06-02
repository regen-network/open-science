import numpy as np
import os
import warnings
warnings.filterwarnings("ignore")

# Geospatial Imports
import fiona
import geopandas as gpd
import rasterio as rio
from rasterio.mask import mask
from rasterstats import zonal_stats


class Image(object):

    def __init__(self, *args):

        if isinstance(args[0], str) and isinstance(args[1], int):
            self.meta = self.get_metadata(args[0])
            self.image_arr = self.read_image(args[0], args[1])
            self.bounds = self.get_bounds(args[0])

        elif isinstance(args[0], (np.ndarray, np.generic)) and isinstance(args[1], dict):
            self.image_arr = args[0]
            self.meta = args[1]

    def duplicate(self):
        return Image(self.image_arr, self.meta)

    def read_image(self, input_file, band=1):
        with rio.open(input_file) as src:
            return src.read(band)

    def update_image(self, new_arr):
        if new_arr.shape == self.image_arr.shape:
            self.image_arr = new_arr
        else:
            print('Unable to update image, dimensions did not match')

    def get_metadata(self, input_file):
        with rio.open(input_file) as src:
            return src.meta

    def get_bounds(self, input_file):
        with rio.open(input_file) as src:
            return src.bounds

    def update_meta(self, field, val):
        try:
            self.meta[field] = val
        except KeyError:
            print(f"{field} unable was not found in image meta.")

    def filter_image(self, min, max):
        self.image_arr = np.where(self.image_arr < min, min, self.image_arr)
        self.image_arr = np.where(self.image_arr > max, max, self.image_arr)

    def set_lower_bound(self, lower_bound, new_min=None):
        if new_min is None:
            self.image_arr = np.where(self.image_arr < lower_bound, lower_bound, self.image_arr)
        else:
            self.image_arr = np.where(self.image_arr < lower_bound, new_min, self.image_arr)

    def set_upper_bound(self, upper_bound, new_max=None):
        if new_max is None:
            self.image_arr = np.where(self.image_arr < upper_bound, upper_bound, self.image_arr)
        else:
            self.image_arr = np.where(self.image_arr < upper_bound, new_max, self.image_arr)

    def mask(self, input_features):
        # create a temporary file
        cwd = os.getcwd()
        to_mask = os.path.join(cwd, 'to_mask.tif')
        self.write_image(to_mask)

        with fiona.open(input_features, 'r') as src:
            shapes = [feature['geometry'] for feature in src]

        with rio.open(to_mask) as src:
            out_image, out_transform = mask(src, shapes, all_touched=True, nodata=-999)

        self.image_arr = out_image
        self.update_meta('height', out_image.shape[1])
        self.update_meta('width', out_image.shape[2])
        self.update_meta('transform', out_transform)
        self.update_meta('nodata', -999)
        os.remove(to_mask)

    def raster_calc(self, eq):
        x = self.image_arr
        self.image_arr = eval(eq)

    def zonal_stats(self, input_feature, stats, prefix=None, output_file=None):
        # read in feature file, add index for spatial join with zstat results
        gdf = gpd.read_file(input_feature, inplace=True)
        gdf['key'] = gdf.index

        # reproject vector file if necessary
        if not self.meta['crs'] == gdf.crs:
            gdf = gdf.to_crs(self.meta['crs'])

        # calculate zonal stats
        z_stats = zonal_stats(gdf, self.image_arr, stats=stats, affine=self.meta['transform'], geojson_out=True)
        for feature in z_stats:
            feature_name = feature['properties']['key']
            for stat in stats:
                if prefix is None:
                    col = stat
                else:
                    col = '{}_{}'.format(prefix, stat)
                gdf.loc[feature_name, col] = feature['properties'][stat]

        # drop temp index and write to file (default file is input)
        if output_file is None:
            output_file = input_feature
            os.remove(input_feature)

        gdf = gdf.drop(columns=['key'], axis=1)
        gdf.to_file(output_file, driver="GPKG")

    def write_image(self, output_file):
        with rio.open(output_file, 'w', **self.meta) as dst:
            dst.write(self.image_arr, indexes=self.meta['count'])
