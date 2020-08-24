#!/usr/bin/env python3
import os
import subprocess
from argparse import ArgumentParser
from pprint import pprint
import xml.etree.ElementTree as ET
from osgeo import gdal
from osgeo import ogr
import numpy as np
import osr
import json
from shutil import copyfile, copytree
from ruamel_yaml import YAML
import config_reader as cfg

def system_call(params):
    fprint(" ".join(params))
    return_code = subprocess.call(params)
    if return_code:
        fprint(return_code)

def fprint(str):
    print('\t', str)

def average_images(dir):
    # average multiple images
    print('AVERAGING IMAGES')
    return

def mosaic_images(im_list, mosaic_settings):
    # mosaic multiple images
    print('BUILDING MOSAIC')

    system_command = ['gdalbuildvrt', 'mosaic.vrt']
    return

# processing the tile
class ProcessTile():

    def __init__(self, config_dict, aoi_file):

        # read in configuration settings
        self.config = config_dict
        fprint('IMAGE SETTINGS: {}'.format(self.config.ard_settings))
        fprint('CLOUD MASK SETTINGS: {}'.format(self.config.cloud_mask_settings))
        fprint('OUTPUT IMAGE SETTINGS: {}'.format(self.config.output_image_settings))

        # output-image-settings
        self.bands = self.config.output_image_settings['bands']
        self.derived_indices = self.config.output_image_settings["vi"]

        self.image_properties = {'resolution' : self.config.output_image_settings['resolution'],
                                 't_srs' : self.config.output_image_settings['t-srs'],
                                 'resampling_method' : self.config.output_image_settings['resampling-method']}

        self.input_features = self.config.output_image_settings['input-features']

        # set working dir
        if self.config.ard_settings['include-in-mosaic'] == True:
            self.output_dir = "/mosaic"
        else:
            self.output_dir = "/output"

    def process_tile(self, input_tile):
        # getting bands paths
        tile_name = input_tile

        # input product type toa (L1C) or boa (L2A)
        producttype = os.path.basename(input_tile)[7:10]
        if producttype == 'L2A':
            all_bands = self._get_boa_band_paths(self._get_metadata_xml(tile_name))
            ref_bands = self._subset_boa_bands(self.bands, all_bands)

        if producttype == 'L1C':
            metadata_xml = self._get_metadata_xml(input_tile)
            all_bands = self._get_toa_band_paths(metadata_xml)
            ref_bands = self._subset_toa_bands(self.bands, all_bands)

        # ATMOSPHERIC CORRECTION - SEN2COR
        if self.config.ard_settings['atm-corr'] == True:
            fprint('RUNNING ATMOSPHERIC CORRECTION - SEN2COR')
            system_command = ['L2A_Process', "--resolution", '10', input_tile]
            system_call(system_command)

            tile_name = self._get_l2a_name(input_tile)
            all_bands = self._get_boa_band_paths(self._get_metadata_xml(tile_name))
            ref_bands = self._subset_boa_bands(self.bands, all_bands)

            copytree(tile_name, self.output_dir + os.sep + os.path.split(tile_name)[1])

        # if output spatial reference is missing epsg code is tile epsg code
        if self.image_properties['t_srs'] == False:
            self.image_properties['t_srs'] = self.get_band_meta(all_bands[list(all_bands.keys())[0]])['epsg']

        # RESAMPLING TO TARGET RESOLUTION
        # resampling to target resolution if bands/image does not meet target resolution
        for key in self.bands:
            if self.get_band_meta(ref_bands[key])['geotransform'][1] != self.image_properties['resolution']:
                fprint('RESAMPLING BAND TO TARGET RESOLUTION: %s' % (key))
                resampled_image = self.rename_image(work_dir, '.tif', os.path.split(os.path.splitext(tile_name)[0])[1], key)
                ref_bands[key] = self.resample_image(ref_bands[key], resampled_image, self.image_properties)

        # DERIVING INDICES
        if self.config.ard_settings["derived-index"] == True:
            fprint('DERIVE INDEX / INDICES')
            vi_band_dict = {
                            'ndvi' : ['B08', 'B04'],
                            'ndwi' : ['B08', 'B11'],
                            'ndti' : ['B11', 'B12'],
                            'crc'  : ['B11', 'B02']
                            }

            derived_bands = {}
            for index in self.derived_indices:
                fprint((index, vi_band_dict[index]))

                if self.config.ard_settings['atm-corr'] == False:
                    if producttype == 'L1C':
                        vi_bands = self._subset_toa_bands(vi_band_dict[index], all_bands)
                        pprint(vi_bands)

                if self.config.ard_settings['atm-corr'] == True or producttype == 'L2A':
                    vi_bands = self._subset_boa_bands(vi_band_dict[index], all_bands)
                    pprint(vi_bands)

                for key in vi_bands.keys():
                    if (self.get_band_meta(vi_bands[key])['geotransform'][1] != self.config.output_image_settings['resolution']):
                        fprint('RESAMPLING BAND TO TARGET RESOLUTION: %s' % (key))
                        resampled_image = self.rename_image(work_dir, '.tif', os.path.split(os.path.splitext(tile_name)[0])[1], key)
                        vi_bands[key] = self.resample_image(vi_bands[key], resampled_image, self.image_properties)

                # write index
                band_meta = self.get_band_meta(vi_bands[key])
                band_meta['dtype'] = 6
                derived_index = self.derive_index(vi_bands[vi_band_dict[index][0]], vi_bands[vi_band_dict[index][1]])
                derived_index_image = self.rename_image(work_dir, '.tif', os.path.splitext(os.path.split(tile_name)[1])[0], index)
                self.write_image(derived_index_image, "GTiff", band_meta, [derived_index])

                derived_bands[index] = derived_index_image

        # SEN2COR CLOUD MASKING ONLY
        if (self.config.ard_settings['cloud-mask'] == True) and (self.config.cloud_mask_settings['sen2cor-scl-codes']):

            if (self.config.ard_settings['atm-corr'] == False) and (producttype == 'L1C'):
                # running sen2cor scene classification only
                fprint('RUNNING SEN2COR SCENE CLASSIFICATION ONLY')
                system_command = ['L2A_Process', "--sc_only", input_tile]
                system_call(system_command)

            scl_image = '.'.join([self._get_boa_band_paths(self._get_metadata_xml(self._get_l2a_name(input_tile)))['SCL_20m']])
            # resampling to target resolution if bands/image does not meet target resolution
            if self.get_band_meta(scl_image)['geotransform'][1] != self.image_properties['resolution']:
                # changing resampling to near since cloud mask image contains discrete values
                _image_properties = self.image_properties.copy()
                _image_properties["resampling_method"] = "near"

                resampled_image = self.rename_image(work_dir, '.tif', os.path.split(os.path.splitext(scl_image)[0])[1], 'resampled')
                scl_image = self.resample_image(scl_image, resampled_image, _image_properties)

            mask = self.binary_mask(self.read_band(scl_image), self.config.cloud_mask_settings['sen2cor-scl-codes'])

            # apply scl_image as mask to ref images
            fprint('APPLYING SEN2COR SCENE CLASSIFICATION MASK TO REF BANDS')
            for key in self.bands:
                band_meta = self.get_band_meta(ref_bands[key])
                masked_array = self.mask_array(mask, self.read_band(ref_bands[key]))
                masked_image = self.rename_image(work_dir, '.tif', os.path.splitext(os.path.basename(ref_bands[key]))[0], 'scl', 'masked')

                self.write_image(masked_image, "GTiff", band_meta, [masked_array])
                ref_bands[key] = masked_image

            # apply scl_image as mask to index images
            fprint('APPLYING SEN2COR SCENE CLASSIFICATION MASK TO INDICES')
            if self.derived_indices != False:
                for key in self.derived_indices:
                    band_meta = self.get_band_meta(derived_bands[key])
                    masked_array = self.mask_array(mask, self.read_band(derived_bands[key]))
                    masked_image = self.rename_image(work_dir, '.tif', os.path.splitext(os.path.basename(derived_bands[key]))[0], 'scl', 'masked')

                    self.write_image(masked_image, "GTiff", band_meta, [masked_array])
                    derived_bands[key] = masked_image

        # FMASK CLOUD MASKING
        if (self.config.ard_settings['cloud-mask'] == True) and (self.config.cloud_mask_settings['fmask-codes']) and (producttype == 'L1C'):
            fprint('RUNNING FMASK CLOUD MASK')
            # running fmask cloud masking
            fmask_image =  + os.sep + '_'.join([os.path.splitext(os.path.split(args.tile)[1])[0], 'FMASK']) + '.tif'
            system_command = ['fmask_sentinel2Stacked.py', '-o', fmask_image, '--safedir', input_tile]
            system_call(system_command)

            # copying fmask image to output dir
            output_image = self.rename_image(self.output_dir, '.tif', os.path.split(os.path.splitext(fmask_image)[0])[1])
            copyfile(fmask_image, output_image)

            # resampling to target resolution if bands/image does not meet target resolution
            if self.get_band_meta(fmask_image)['geotransform'][1] != self.image_properties['resolution']:
                # changing resampling to near since cloud mask image contains discrete values
                _image_properties = self.image_properties.copy()
                _image_properties["resampling_method"] = "near"
                fmask_image = self.resample_image(fmask_image, 'resampled', _image_properties)

            # applying fmask as mask to ref images
            fprint('APPLYING FMASK CLOUD MASK')
            mask = self.binary_mask(self.read_band(fmask_image), self.config.cloud_mask_settings['fmask-codes'])
            for key in self.bands:
                band_meta = self.get_band_meta(ref_bands[key])
                masked_array = self.mask_array(mask, self.read_band(ref_bands[key]))
                masked_image = self.rename_image(work_dir, '.tif', os.path.splitext(os.path.basename(ref_bands[key]))[0], 'fmask', 'masked')
                self.write_image(masked_image, "GTiff", band_meta, [masked_array])
                ref_bands[key] = masked_image

            # apply fmask as mask to index images
            fprint('APPLYING FMASK CLOUD MASK TO INDICES')
            if self.derived_indices != False:
                for key in self.derived_indices:
                    band_meta = self.get_band_meta(derived_bands[key])
                    masked_array = self.mask_array(mask, self.read_band(derived_bands[key]))
                    masked_image = self.rename_image(work_dir, '.tif', os.path.splitext(os.path.basename(derived_bands[key]))[0], 'fmask', 'masked')
                    self.write_image(masked_image, "GTiff", band_meta, [masked_array])
                    derived_bands[key] = masked_image

        # CALIBRATION
        if self.config.ard_settings['calibrate'] == True:
            fprint('CALIBRATING BANDS')
            for key in self.bands:
                fprint('CALIBRATING BAND %s' % (key))
                ref_bands[key] = self.calibrate('.'.join([ref_bands[key]]))

        # REPROJECTION
        # ref images
        for key in ref_bands:
            if self.get_band_meta(ref_bands[key])['epsg'] != str(self.image_properties['t_srs']):
                fprint('REPROJECTING BAND %s' % (key))
                ref_bands[key] = self.warp_image(ref_bands[key], 'resampled', self.image_properties)

        # index images
        if self.config.ard_settings["derived-index"] == True:
            for key in derived_bands:
                if self.get_band_meta(derived_bands[key])['epsg'] != str(self.image_properties['t_srs']):
                    fprint('REPROJECTING BAND %s' % (key))
                    derived_bands[key] = self.warp_image(derived_bands[key], 'resampled', self.image_properties)

        # STACKING
        # onyl ref images
        if self.config.ard_settings['stack'] == True:
            fprint('STACKING BANDS')
            arrays = []
            if len(self.bands) > 1:
                for key in self.bands:
                    fprint('STACKING BAND %s' % (key))
                    band_meta = self.get_band_meta(ref_bands[key])
                    arrays.append(self.read_band(ref_bands[key]))
                stacked_image = self.rename_image(work_dir, '.tif', os.path.splitext(os.path.split(tile_name)[1])[0], 'stacked')
                self.write_image(stacked_image, "GTiff", band_meta, arrays)

                ref_bands = {}
                ref_bands['stacked'] = stacked_image

        # add ref images dict + index images dict and loop
        if self.config.ard_settings["derived-index"] == True:
            ref_bands.update(derived_bands)

        # copying output images to /output directory
        for key in ref_bands.keys():
            output_image = self.rename_image(self.output_dir, '.tif', os.path.split(os.path.splitext(tile_name)[0])[1], key)
            copyfile(ref_bands[key], output_image)

        # CLIPPING / CROP_TO_CUTLINE
        if self.config.ard_settings['clip'] == True:
            # create subdirectory
            self.output_dir = self.output_dir + os.sep + 'clipped'
            if not os.path.exists(self.output_dir):
                os.mkdir(self.output_dir)

            fprint('CROPPING TO CUTLINE')
            # reprojecting input_features to target_srs if not common projection
            features_epsg = self.get_vector_epsg(self.input_features)
            if features_epsg != str(self.image_properties['t_srs']):
                fprint('REPROJECTING INPUT FEATURES TO TARGET PROJECTION')
                t_srs_feature_aoi =  + os.sep + "_".join([os.path.splitext(os.path.split(self.input_features)[1])[0], str(self.image_properties['t_srs'])]) + '.geojson'
                system_command = ['ogr2ogr', "-t_srs", 'EPSG:' + str(self.image_properties['t_srs']), t_srs_feature_aoi, self.input_features]
                system_call(system_command)
                self.input_features = t_srs_feature_aoi

            src = ogr.Open(self.input_features, 0)
            layer = src.GetLayer()
            count = layer.GetFeatureCount()
            for feature in layer:
                feature_id = feature.GetFID()

                feature_shp = self.rename_image(work_dir, '.geojson', os.path.splitext(os.path.split(self.input_features)[1])[0], 'FEATURE_ID', str(feature_id))

                ftr_drv = ogr.GetDriverByName('Esri Shapefile')
                out_feature = ftr_drv.CreateDataSource(feature_shp)
                lyr = out_feature.CreateLayer('poly', layer.GetSpatialRef(), ogr.wkbPolygon)
                feat = lyr.CreateFeature(feature.Clone())
                out_feature = None

                # cropping reflectance band image chips
                for key in ref_bands:
                    if count == 1:
                        image_chip = self.rename_image(self.output_dir, '.tif', os.path.split(os.path.splitext(tile_name)[0])[1], key, 'clipped')

                    if count > 1:
                        # create subdirectory
                        self.subdir = self.output_dir + os.sep + str(feature_id)
                        if not os.path.exists(self.subdir):
                            os.mkdir(self.subdir)

                        image_chip = self.rename_image(self.subdir, '.tif', os.path.split(os.path.splitext(tile_name)[0])[1], key, 'FEATURE_ID', str(feature_id), 'clipped')

                    # cropping to cutline bands
                    system_command = ['gdalwarp', "-cutline", feature_shp, '-crop_to_cutline', ref_bands[key], image_chip, '-overwrite']
                    system_call(system_command)

    # metadata xml and parsing operations
    def _get_l2a_name(self, input_tile):
        for safe in os.listdir():
            tile_name =  + os.sep + safe
            if os.path.isdir(tile_name) and (os.path.split(tile_name)[1][7:10] == 'L2A'):
                return(tile_name)

    def _get_metadata_xml(self, input_tile):
        for i in os.listdir(input_tile):
            if (os.path.splitext(i)[1] == '.xml') and ('MTD' in i):
                metadata_xml = input_tile + os.sep + i
        return(metadata_xml)

    def _get_boa_band_paths(self, metadata_xml):
        band_paths = {}
        root = ET.parse(metadata_xml)
        product = root.findall('.//Product_Organisation/Granule_List/Granule')
        for res_dir in product:
            for band in res_dir.findall('IMAGE_FILE'):
                #if band.text[-7:-4] in self.bands:
                band_paths[band.text[-7:]] = os.path.split(metadata_xml)[0] + os.sep + band.text + '.jp2'
        return(band_paths)

    def _get_toa_band_paths(self, metadata_xml):
        band_paths = {}
        root = ET.parse(metadata_xml)
        product = root.findall('.//Product_Organisation/Granule_List/Granule')
        for res_dir in product:
            for band in res_dir.findall('IMAGE_FILE'):
                #if band.text[-3:] in self.bands:
                band_paths[band.text[-3:]] = os.path.split(metadata_xml)[0] + os.sep + band.text + '.jp2'
        return(band_paths)

    def _subset_toa_bands(self, subset_bands, all_bands):
        ref_bands = {}
        for key in all_bands.keys():
            if key in subset_bands:
                ref_bands[key] = all_bands[key]
        return(ref_bands)

    def _subset_boa_bands(self, subset_bands, band_paths):
        subset_band_paths = {}
        for band in subset_bands:
            key = '_'.join([band, '10m'])
            if key in band_paths.keys():
                subset_band_paths[key[:3]] = band_paths[key]
            if key not in band_paths.keys():
                key = '_'.join([band, '20m'])
                subset_band_paths[key[:3]] = band_paths[key]
        return(subset_band_paths)

    def rename_image(self, basedir, extension, *argv):
        new_name = basedir + os.sep + "_".join(argv) + extension
        return(new_name)

    # raster operations
    def resample_image(self, image, resampled_image, img_prop):
        fprint('Resolution does not meet target_resolution, resampling %s' % (image))
        system_command = ['gdal_translate', "-tr", str(img_prop['resolution']), str(img_prop['resolution']), '-r', str(img_prop['resampling_method']), image, resampled_image]
        system_call(system_command)
        return(resampled_image)

    def warp_image(self, image, suffix, img_prop):
        warped_image =  + os.sep + '_'.join([os.path.splitext(os.path.basename(image))[0], suffix, str(img_prop['resolution']), img_prop['resampling_method'], str(img_prop['t_srs'])]) + '.tif'
        system_command = ['gdalwarp', "-tr", str(img_prop['resolution']), str(img_prop['resolution']), '-t_srs', 'EPSG:' + str(img_prop['t_srs']),'-r', img_prop['resampling_method'], image, warped_image, '-overwrite']
        system_call(system_command)
        return(warped_image)

    def calibrate(self, band_path):
        calibrated_band =  + os.sep + os.path.split(os.path.splitext(band_path)[0])[1] + '.tif'
        band_meta = self.get_band_meta(band_path)
        src = gdal.Open(band_path)
        scale_factor = 10000.
        dst = src.GetRasterBand(1).ReadAsArray() / scale_factor
        band_meta['dtype'] = 6
        self.write_image(calibrated_band, 'GTiff', band_meta, [dst])
        return(calibrated_band)

    def read_band(self, band_path):
        src = gdal.Open(band_path)
        return(src.GetRasterBand(1).ReadAsArray())

    def get_band_arrays(self, bands):
        band_arrays = []
        for band in bands:
            band_arrays.append(self.read_band(band))
        return(band_arrays)

    def get_band_meta(self, img_file):
        band_meta = {}
        src = gdal.Open(img_file)
        band_meta['band_num'] = src.RasterCount
        band_meta['geotransform'] = list(src.GetGeoTransform())
        band_meta['crs'] = src.GetProjectionRef()
        band_meta['epsg'] = osr.SpatialReference(wkt=src.GetProjectionRef()).GetAttrValue('AUTHORITY', 1)
        band_meta['X'] = src.RasterXSize
        band_meta['Y'] = src.RasterYSize
        band_meta['dtype'] = src.GetRasterBand(1).DataType
        band_meta['datatype'] = gdal.GetDataTypeName(band_meta["dtype"])
        band_meta['nodata'] = src.GetRasterBand(1).GetNoDataValue()
        band_meta['nodata'] = 0
        return(band_meta)

    def binary_mask(self, scl, pixel_values):
        mask = np.zeros(scl.shape)
        for pixel_value in pixel_values:
            mask = np.ma.masked_where(scl == pixel_value, mask).filled(1)
        return(mask)

    def mask_array(self, mask, array):
        return(np.ma.masked_where(mask == 0, array).filled(0))

    def derive_index(self, nir, red):
        fprint('DERIVING NDVI')
        nir, red = self.read_band(nir) / float(10000), self.read_band(red) / float(10000)
        ndvi = (nir - red) / (nir + red).astype(np.float32)
        ndvi = np.ma.masked_where(ndvi > 1, ndvi).filled(0)
        ndvi = np.ma.masked_where(ndvi < -1, ndvi).filled(0)
        return(ndvi)

    def write_image(self, out_name, driver, band_meta, arrays):
        fprint('WRITING IMAGE : {}'.format(out_name))
        driver = gdal.GetDriverByName(driver)
        dataset_out = driver.Create(out_name, band_meta["X"], band_meta["Y"], len(arrays), band_meta["dtype"])
        dataset_out.SetGeoTransform(band_meta["geotransform"])
        dataset_out.SetProjection(band_meta["crs"])
        dataset_out.SetMetadataItem('AREA_OR_POINT', 'Area')
        for i in range(len(arrays)):
            band = dataset_out.GetRasterBand(i + 1)
            band.WriteArray(arrays[i])
            band.SetNoDataValue(band_meta['nodata'])
        dataset_out = None

    # vector operations
    def get_vector_epsg(self, shp):
        src = ogr.Open(shp, 0)
        layer = src.GetLayer()
        srs = layer.GetSpatialRef()
        return(srs.GetAttrValue("AUTHORITY", 1))



if __name__ == "__main__":
    # parse command line arguments
    desc = "Sentinel-2 Analysis Ready Data"
    parser = ArgumentParser(description=desc)
    parser.add_argument("--tiles", "-t", type=str, dest='tiles', help="Sentinel-2 data product name", required=True)
    args = parser.parse_args()

    # data dir
    data_dir = args.tiles

    # tiles
    tile_list = os.listdir(data_dir)

    # yaml
    config_file = os.path.dirname(os.path.realpath(__file__)) + os.sep + 'config.yml'

    # geojson
    aoi_file = os.path.dirname(os.path.realpath(__file__)) + os.sep + 'aoi.geojson'

    # WORKDIR
    work_dir = "/work"
    mosaic_dir  = "/work/mosaic"

    # extract image metadata
    ard_settings = cfg.ConfigReader(config_file, aoi_file)

    # process images
    for image_config in ard_settings.image_list:
        input_tile = data_dir + os.sep + image_config.tile_name
        if os.path.isdir(input_tile) == True:
            print('PROCESSING IMAGE: ', image_config.tile_name)
            pg = ProcessTile(image_config, aoi_file)
            pg.process_tile(input_tile)
        else:
            print('Unable to process tile:', image_config.tile_name)

    # mosaic images
    if ard_settings.batch_settings['mosaic'] == True:
        mosaic_images()

    # average images
    if ard_settings.batch_settings['average_images'] == True:
        average_images()
