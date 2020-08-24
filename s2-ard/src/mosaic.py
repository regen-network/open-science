import os
import glob
import subprocess
from argparse import ArgumentParser
from config_reader import ConfigReader

def system_call(params):
    print(" ".join(params))
    return_code = subprocess.call(params)
    if return_code:
        print(return_code)


def build_mosaic(image_dir, mosaic_settings):
    # build image list
    tile_list = (file for file in os.listdir(image_dir)
                    if os.path.isfile(os.path.join(image_dir, file)))

    # mosaics to build based on extension (stacked, ndvi, etc...)
    file_extensions = list(set([tile[61:] for tile in tile_list]))

    # ordered list of images to mosaic
    mosaic_list = [name[:60] for name in mosaic_settings['mosaic-order']]
    image_dates = [tile[11:19] for tile in mosaic_list]

    for extension in file_extensions:
        # create a list of images to mosaic
        to_mosaic = glob.glob('{}/*{}'.format(working_dir, extension))
        for image in to_mosaic:
            if os.path.split(image)[1][:60] not in mosaic_list:
                print('MOSAIC ERROR: {} not included in list of images to mosaic.'.format(image))
                return

        # create an ordered list of images to mosaic
        mosaic_bands = [x for _,x in sorted(zip(mosaic_list, to_mosaic))]

        # build mosaic
        mosaic_vrt = image_dir + os.sep + '_'.join(image_dates + [extension[:-4], 'mosaic']) + '.vrt'
        system_command = ['gdalbuildvrt', mosaic_vrt, '-r', mosaic_settings['resampling-method']] + mosaic_bands
        system_call(system_command)

        output_image = mosaic_vrt[:-4] + '.tif'

        # convert mosaic to geotiff
        system_command = ["gdal_translate", "-of", "GTiff", mosaic_vrt, output_image]
        system_call(system_command)


if __name__ == "__main__":

    config_file = os.path.dirname(os.path.realpath(__file__)) + os.sep + 'config.yml'

    ard_settings = ConfigReader(config_file, 'haha')

    working_dir = "/mosaic/mosaic"

    output_mosaic = build_mosaic(working_dir, ard_settings.mosaic_settings)
