from ruamel_yaml import YAML
import os

# reading the configuration file
class ConfigReader(object):

    def __init__(self, yaml_file, geojson_file):

        # read in YML file
        with open(yaml_file) as stream:
            yaml = YAML()
            config = yaml.load(stream)

        # validate batch settings
        try:
            self.batch_keywords = ["mosaic", "average-images", "mosaic-in-average"]
            self.batch_settings = {}
            for key in self.batch_keywords:
                if key in dict(config['batch-settings']).keys():
                    self.batch_settings[key] = dict(config['batch-settings'])[key]
                if key not in dict(config['batch-settings']).keys():
                    self.batch_settings[key] = False
        except Exception:
            raise IOError('in YAML file batch-settings not defined')

        # validate mosaic settings
        try:
            self.mosaic_keywords = ["resolution", "resampling-method"]
            self.mosaic_settings = {}
            for key in self.mosaic_keywords:
                if key in dict(config['mosaic-settings']).keys():
                    self.mosaic_settings[key] = dict(config['mosaic-settings'])[key]
                # default settings are always false
                if key not in dict(config['mosaic-settings']).keys():
                    self.mosaic_settings[key] = False

            self.mosaic_settings['mosaic-order'] = []
            for i in config['mosaic-settings']['mosaic-order']:
                self.mosaic_settings['mosaic-order'].append(config['mosaic-settings']['mosaic-order'][i])

        except Exception:
            raise IOError('in YAML file mosaic-settings not defined')


        self.image_list = []
        for image_yaml in config['image-list']:
            image_config = config['image-list'][image_yaml]
            image_settings = ImageReader(image_config, geojson_file)
            self.image_list.append(image_settings)

# reading of image objects in config file
class ImageReader(object):

    def __init__(self, config, geojson_file):

        # validate tile-name
        try:
            self.tile_name = config['tile-name']
        except Exception:
            raise IOError('in YAML file tile-name not defined')


        # validate ard-settings
        try:
            self.ard_keywords = ["atm-corr", "cloud-mask", "stack", "calibrate", "clip", "derived-index", "include-in-mosaic", "include-in-average"]

            self.ard_settings = {}
            for key in self.ard_keywords:
                if key in dict(config['ard-settings']).keys():
                    self.ard_settings[key] = dict(config['ard-settings'])[key]
                # default ard settings are always false
                if key not in dict(config['ard-settings']).keys():
                    self.ard_settings[key] = False
        except Exception:
            raise IOError('in YAML file ard-settings is not defined for: ', self.tile_name)

        # validate cloud-mask-settings
        if self.ard_settings['cloud-mask'] == True:
            try:
                self.cloud_mask_keywords = ["sen2cor-scl-codes", "fmask-codes"]

                self.cloud_mask_settings = {}
                for key in self.cloud_mask_keywords:
                    if key in dict(config['cloud-mask-settings']).keys():
                        self.cloud_mask_settings[key] = dict(config['cloud-mask-settings'])[key]

                    if key not in dict(config['cloud-mask-settings']).keys():
                        self.cloud_mask_settings[key] = False
            except Exception:
                raise IOError('in YAML file cloud-mask-settings is not defined for: ', self.tile_name)

        if self.ard_settings['cloud-mask'] == False:
            self.cloud_mask_settings = False

        # validate output-image-settings
        try:
            self.output_image_keywords = ["bands", "vi", "resampling-method", "t-srs", "resolution"]

            self.output_image_settings = {}
            for key in self.output_image_keywords:
                if key in dict(config['output-image-settings']).keys():
                    self.output_image_settings[key] = dict(config['output-image-settings'])[key]
                # default output_image_settings are always false
                if key not in dict(config['output-image-settings']).keys():
                    self.output_image_settings[key] = False

            # default keywords settings
            if 'bands' not in dict(config['output-image-settings']).keys():
                self.output_image_settings['bands'] = [] # NIR-RED-GREEN Band Combinations
            if 'resolution' not in dict(config['output-image-settings']).keys():
                self.output_image_settings['resolution'] = 10
            if 'resampling-method' not in dict(config['output-image-settings']).keys():
                self.output_image_settings['resampling-method'] = 'near'

            if os.path.exists(geojson_file):
                self.output_image_settings['input-features'] = geojson_file
            if not os.path.exists(geojson_file):
                self.output_image_settings['input-features'] = False

            if (self.ard_settings['clip'] == True) and (self.output_image_settings['input-features'] == False):
                print('in YAML file input_features as the crop-to-cutline is not defined')
                exit(1)

        except Exception:
            print('in YAML file output-image-settings is not defined for: {}. Default settings are used.'.format(self.tile_name))
