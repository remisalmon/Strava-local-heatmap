# Copyright (c) 2018 Remi Salmon
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# imports
import os
import re
import glob
import time
import argparse
import urllib.error
import urllib.request

import numpy as np
import matplotlib.pyplot as plt

# globals
PLT_COLORMAP = 'hot' # matplotlib color map (see https://matplotlib.org/examples/color/colormaps_reference.html)
MAX_TILE_COUNT = 100 # maximum number of OSM tiles to download

OSM_TILE_SERVER = 'https://maps.wikimedia.org/osm-intl/{}/{}/{}.png' # OSM tiles url (see https://wiki.openstreetmap.org/wiki/Tile_servers)
OSM_TILE_SIZE = 256 # OSM tile size in pixels
OSM_MAX_ZOOM = 19 # OSM max zoom level

# functions
def deg2num(lat_deg, lon_deg, zoom): # return OSM tile x,y from lat,lon in degrees (from https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames)
  lat_rad = np.radians(lat_deg)
  n = 2.0 ** zoom
  xtile = int((lon_deg + 180.0) / 360.0 * n)
  ytile = int((1.0 - np.log(np.tan(lat_rad) + (1 / np.cos(lat_rad))) / np.pi) / 2.0 * n)

  return xtile, ytile

def num2deg(xtile, ytile, zoom): # return lat,lon in degrees from OSM tile x,y (from https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames)
  n = 2.0 ** zoom
  lon_deg = xtile / n * 360.0 - 180.0
  lat_rad = np.arctan(np.sinh(np.pi * (1 - 2 * ytile / n)))
  lat_deg = np.degrees(lat_rad)

  return lat_deg, lon_deg

def deg2xy(lat_deg, lon_deg, zoom): # return OSM global x,y coordinates from lat,lon in degrees
    lat_rad = np.radians(lat_deg)
    n = 2.0 ** zoom
    x = (lon_deg + 180.0) / 360.0 * n
    y = (1.0 - np.log(np.tan(lat_rad) + (1 / np.cos(lat_rad))) / np.pi) / 2.0 * n

    return x, y

def box_filter(image, w_box): # return image filtered with box filter
    box = np.ones((w_box, w_box))/(w_box**2)

    image_fft = np.fft.rfft2(image)
    box_fft = np.fft.rfft2(box, s = image.shape)

    image = np.fft.irfft2(image_fft*box_fft)

    return image

def download_tile(tile_url, tile_file): # download tile from url and save to file
    request = urllib.request.Request(tile_url, headers = {'User-Agent':'Mozilla/5.0'})

    try:
        response = urllib.request.urlopen(request)

    except urllib.error.URLError as e: # (see https://docs.python.org/3/howto/urllib2.html)
        print('ERROR downloading tile from OSM server failed')

        if hasattr(e, 'reason'):
            print(e.reason)

        elif hasattr(e, 'code'):
            print(e.code)

        return False

    else:
        with open(tile_file, 'wb') as file:
            file.write(response.read())

        time.sleep(0.1)

    return True

def main(args):
    gpx_dir = args.dir # string
    gpx_glob = args.filter # string
    gpx_year = args.year # string
    lat_bound_min, lat_bound_max, lon_bound_min, lon_bound_max = args.bounds # float
    heatmap_file = args.output # string
    heatmap_zoom = args.zoom # int
    sigma_pixels = args.sigma # int
    use_csv = args.csv # bool
    use_cumululative_distribution = not args.no_cdist # bool

    heatmap_zoom = min(heatmap_zoom, OSM_MAX_ZOOM)

    try:
        cmap = plt.get_cmap(PLT_COLORMAP)

    except:
        exit('ERROR colormap {} does not exists'.format(PLT_COLORMAP))

    # find GPX files
    gpx_files = glob.glob('{}/{}'.format(gpx_dir, gpx_glob))

    if not gpx_files:
        exit('ERROR no data matching {}/{}'.format(gpx_dir, gpx_glob))

    # read GPX files
    lat_lon_data = []

    for gpx_file in gpx_files:
        print('reading {}...'.format(gpx_file))

        with open(gpx_file) as file:
            for line in file:
                if '<time' in line:
                    tmp = re.findall('[0-9]{4}', line)

                    if gpx_year in (tmp[0], 'all'):
                        for line in file:
                            if '<trkpt' in line:
                                tmp = re.findall('-?[0-9]*[.]?[0-9]+', line)

                                lat_lon_data.append([float(tmp[0]), float(tmp[1])])

                    else:
                        break

    if not lat_lon_data:
        exit('ERROR no data matching {}/{} with year {}'.format(gpx_dir, gpx_glob, gpx_year))

    print('Processing GPX data...')

    lat_lon_data = np.array(lat_lon_data)

    # crop data to bounding box
    lat_lon_data = lat_lon_data[np.logical_and(lat_lon_data[:, 0] > lat_bound_min, lat_lon_data[:, 0] < lat_bound_max), :]
    lat_lon_data = lat_lon_data[np.logical_and(lat_lon_data[:, 1] > lon_bound_min, lat_lon_data[:, 1] < lon_bound_max), :]

    if lat_lon_data.size == 0:
        exit('ERROR no data matching {}/{} with bound {},{},{},{}'.format(gpx_dir, gpx_glob, lat_bound_min, lat_bound_max, lon_bound_min, lon_bound_max))

    # find min, max tile x,y coordinates
    lat_min = lat_lon_data[:, 0].min()
    lat_max = lat_lon_data[:, 0].max()
    lon_min = lat_lon_data[:, 1].min()
    lon_max = lat_lon_data[:, 1].max()

    x_tile_min, y_tile_max = deg2num(lat_min, lon_min, heatmap_zoom)
    x_tile_max, y_tile_min = deg2num(lat_max, lon_max, heatmap_zoom)

    tile_count = (x_tile_max-x_tile_min+1)*(y_tile_max-y_tile_min+1)

    if tile_count > MAX_TILE_COUNT:
        exit('ERROR zoom value too high, too many tiles to download')

    # download tiles
    if not os.path.exists('tiles'):
        os.makedirs('tiles')

    i = 0
    for x in range(x_tile_min, x_tile_max+1):
        for y in range(y_tile_min, y_tile_max+1):
            tile_url = OSM_TILE_SERVER.format(heatmap_zoom, x, y)

            tile_file = 'tiles/tile_{}_{}_{}.png'.format(heatmap_zoom, x, y)

            if not glob.glob(tile_file):
                i += 1

                print('downloading map tile {}/{}...'.format(i, tile_count))

                if not download_tile(tile_url, tile_file):
                    tile_image = np.ones((OSM_TILE_SIZE, OSM_TILE_SIZE, 3))

                    plt.imsave(tile_file, tile_image)

    print('Creating heatmap...')

    # create supertile
    supertile_size = ((y_tile_max-y_tile_min+1)*OSM_TILE_SIZE, (x_tile_max-x_tile_min+1)*OSM_TILE_SIZE, 3)

    supertile = np.zeros(supertile_size)

    for x in range(x_tile_min, x_tile_max+1):
        for y in range(y_tile_min, y_tile_max+1):
            tile_file = 'tiles/tile_{}_{}_{}.png'.format(heatmap_zoom, x, y)

            tile = plt.imread(tile_file)

            i = y-y_tile_min
            j = x-x_tile_min

            supertile[i*OSM_TILE_SIZE:i*OSM_TILE_SIZE+OSM_TILE_SIZE, j*OSM_TILE_SIZE:j*OSM_TILE_SIZE+OSM_TILE_SIZE, :] = tile[:, :, :3]

    # convert supertile to grayscale and invert colors
    supertile = 0.2126*supertile[:, :, 0]+0.7152*supertile[:, :, 1]+0.0722*supertile[:, :, 2]

    supertile = 1-supertile

    supertile = np.dstack((supertile, supertile, supertile))

    # fill trackpoints data
    data = np.zeros(supertile_size[:2])

    for lat, lon in lat_lon_data:
        x, y = deg2xy(lat, lon, heatmap_zoom)

        i = int(np.round((y-y_tile_min)*OSM_TILE_SIZE))
        j = int(np.round((x-x_tile_min)*OSM_TILE_SIZE))

        data[i-sigma_pixels:i+sigma_pixels+1, j-sigma_pixels:j+sigma_pixels+1] += 1 # pixels are centered on the trackpoint

    # threshold trackpoints accumulation to avoid large local maxima
    if use_cumululative_distribution:
        pixel_res = 156543.03*np.cos(np.radians(np.mean(lat_lon_data[:, 0])))/(2**heatmap_zoom) # (see https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Resolution_and_Scale)

        m = (1.0/5.0)*pixel_res*len(gpx_files) # trackpoints max accumulation per pixel = 1/5 (trackpoints/meters) * pixel_res (meters/pixel) per activity (Strava records trackpoints every 5 meters in average for cycling activites)

    else:
        m = 1.0

    data[data > m] = m # threshold data to max accumulation of trackpoints

    # kernel density estimation = convolution with (almost-)Gaussian kernel
    w_filter = int(np.sqrt(12.0*sigma_pixels**2+1.0)) # (see https://www.peterkovesi.com/papers/FastGaussianSmoothing.pdf)

    data = box_filter(data, w_filter)

    # normalize data to [0,1]
    data = (data-data.min())/(data.max()-data.min())

    # colorize data and remove background color
    data_color = cmap(data)

    data_color[(data_color == cmap(0)).all(2)] = [0.0, 0.0, 0.0, 1.0]

    data_color = data_color[:, :, :3]

    # create color overlay
    supertile_overlay = np.zeros(supertile_size)

    for c in range(3):
        supertile_overlay[:, :, c] = (1.0-data_color[:, :, c])*supertile[:, :, c]+data_color[:, :, c]

    # save image
    if not os.path.splitext(heatmap_file)[1] == '.png':
        heatmap_file = '{}.png'.format(os.path.splitext(heatmap_file)[0])

    plt.imsave(heatmap_file, supertile_overlay)

    print('Saved {}'.format(heatmap_file))

    # save csv file
    if use_csv:
        csv_file = '{}.csv'.format(os.path.splitext(heatmap_file)[0])

        with open(csv_file, 'w') as file:
            file.write('latitude,longitude,intensity\n')

            for i in range(data.shape[0]):
                for j in range(data.shape[1]):
                    if data[i, j] > 0.1:
                        x = x_tile_min+j/OSM_TILE_SIZE
                        y = y_tile_min+i/OSM_TILE_SIZE

                        lat, lon = num2deg(x, y, heatmap_zoom)

                        file.write('{},{},{}\n'.format(lat, lon, data[i,j]))

        print('Saved {}'.format(csv_file))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'Generate a local heatmap from Strava GPX files', epilog = 'Report issues to https://github.com/remisalmon/strava-local-heatmap')

    parser.add_argument('--dir', default = 'gpx', help = 'GPX files directory  (default: gpx)')
    parser.add_argument('--year', default = 'all', help = 'GPX files year filter (default: all)')
    parser.add_argument('--filter', default = '*.gpx', help = 'GPX files glob filter (default: *.gpx)')
    parser.add_argument('--bounds', type = float, nargs = 4, default = [-90, +90, -180, +180], help = 'heatmap bounding box coordinates as lat_min, lat_max, lon_min, lon_max (default: -90 +90 -180 +180)')
    parser.add_argument('--output', default = 'heatmap.png', help = 'heatmap name (default: heatmap.png)')
    parser.add_argument('--zoom', type = int, default = 10, help = 'heatmap zoom level 0-19 (default: 10)')
    parser.add_argument('--sigma', type = int, default = 1, help = 'heatmap Gaussian kernel sigma in pixels (default: 1)')
    parser.add_argument('--csv', action = 'store_true', help = 'also save the heatmap data to a CSV file')
    parser.add_argument('--no-cdist', action = 'store_true', help = 'disable cumulative distribution of trackpoints (uniform distribution)')

    args = parser.parse_args()

    main(args)
