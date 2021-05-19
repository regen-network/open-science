import os
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio as rio
from rasterstats import point_query, zonal_stats
from pyproj import Proj, transform


class SampleRaster(object):

    def __init__(self, sample_locations, image_list):

        # list of rasters to sample
        self.raster_list = image_list

        # read in sampling point file
        self.sample_locations = gpd.read_file(sample_locations)
        self.sample_locations['key'] = self.sample_locations.index
        self.sample_locations = self.sample_locations.dropna()

    def get_raster_meta(self, input_raster):
        with rio.open(input_raster) as src:
            return src.meta

    def extract_single_value(self, point, raster, band):
        return point_query(point, raster, band, interpolate='nearest')[0]

    def focal_mean(self, centroid, raster, band):
        # read in raster dataset and fill array
        ds = rio.open(raster)
        arr = ds.read(band)

        # get array index for point location
        i, j = ds.index(centroid.x, centroid.y)
        ds.close()

        # calculate focal mean
        offset = 1  # number of rows around point to include in window
        window = arr[i-offset:i+offset+1, j-offset:j+offset+1]
        windowSum = np.sum(window)
        focalMean = (float(windowSum) / np.size(window))

        return focalMean

    def extract_zonal_value(self, sample_locations, raster, band_index, band_name, affine):

        zonal_values = {
            'Sample Location': [],
            band_name: []
        }
        z_stats = zonal_stats(sample_locations, raster, affine=affine, band=band_index, stats=['mean'], geojson_out=True)
        for feature in z_stats:
            zonal_values['Sample Location'].append(feature['properties']['Sample Location'])
            zonal_values[band_name].append(feature['properties']['mean'])

        return pd.DataFrame(zonal_values)

    def append_locations(self, t_srs):
        inProj = Proj(self.sample_locations.crs)
        outProj = Proj(t_srs)

        coords = []
        for index, row in self.sample_locations.iterrows():
            x, y = transform(inProj, outProj, row.geometry.x, row.geometry.y)
            coords.append([row.key] + [x, y])

        cols = ['key', 'Lon', 'Lat']
        coords_df = pd.DataFrame(coords, columns=cols)
        self.sample_locations = self.sample_locations.merge(coords_df, on='key')

    def sample_raster_values(self, method):

        for raster in self.raster_list:
            # get raster metadata
            print('\tProcessing Raster: %s' % os.path.split(raster['name'])[1])
            raster_meta = self.get_raster_meta(raster['name'])
            band_count = raster_meta['count']
            band_names = raster['band_list']

            # reproject sampling points to match input raster
            points_df = self.sample_locations
            if not raster_meta['crs'] == points_df.crs:
                points_df = points_df.to_crs(raster_meta['crs'])

            # extract spectral values
            if method == 'zonal':
                band_indices = [i+1 for i in range(band_count)]
                for index, name in zip(band_indices, band_names):
                    svals_df = self.extract_zonal_value(self.sample_locations, raster['name'], index, name, raster_meta['transform'])
                    self.sample_locations = self.sample_locations.merge(svals_df, on='Sample Location')
            else:
                spectral_values = []
                for index, row in points_df.iterrows():
                    if row.geometry.geom_type == "MultiPoint":
                        sample_location = row.geometry[0]
                    if row.geometry.geom_type == "Point":
                        sample_location = row.geometry
                    if method == 'point':
                        r_vals = [self.extract_single_value(sample_location, raster['name'], i+1) for i in range(band_count)]
                    elif method == 'fmean':
                        r_vals = [self.focal_mean(sample_location, raster['name'], i+1) for i in range(band_count)]
                    else:
                        raise ValueError('Extraction method must be set to point or mean')
                    spectral_values.append([row.key] + r_vals)

                # merge datasets
                cols = ['key'] + band_names
                svals_df = pd.DataFrame(spectral_values, columns=cols)
                self.sample_locations = self.sample_locations.merge(svals_df, on='key')

    def write_file(self, output_file):
        # write smoothed data to csv
        self.sample_locations = self.sample_locations.drop(['geometry', 'key'], axis=1)
        sample_locations_avg = self.sample_locations.groupby('Sample Location', as_index=False).mean()
        sample_locations_avg.to_csv(output_file, index=False)
