import os
import confuse
from confuse import MappingTemplate


class ConfigReader:

    def __init__(self, yaml_file, data_dir):
        self.data_dir = data_dir
        self.config = confuse.Configuration('ConfigReader')
        self.config.set_file(yaml_file)

    def validate_path(self, filename):
        path = os.path.join(self.data_dir, filename)
        if not os.path.isfile(path):
            raise FileNotFoundError(os.path.split(path)[1])
        return path


class RasterReader(ConfigReader):

    def __init__(self, yaml_file, data_dir):

        ConfigReader.__init__(self, yaml_file, data_dir)

        # raster list
        self.raster_list = []
        for raster in self.config['raster_list'].values():
            name = self.validate_path(raster['name'].as_str())
            band_list = raster['band_list'].get()
            self.raster_list.append({'name': name, 'band_list': band_list})
