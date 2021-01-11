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
import glob
import time
import argparse
import urllib.error
import urllib.request

import numpy as np
import matplotlib.pyplot as plt

# globals
PLT_COLORMAP = 'hot' # matplotlib color map
MAX_TILE_COUNT = 100 # maximum number of tiles to download
MAX_HEATMAP_SIZE = (2160, 3840) # maximum heatmap size in pixel

OSM_TILE_SERVER = 'https://maps.wikimedia.org/osm-intl/{}/{}/{}.png' # OSM tile url from https://wiki.openstreetmap.org/wiki/Tile_servers
OSM_TILE_SIZE = 256 # OSM tile size in pixel
OSM_MAX_ZOOM = 19 # OSM maximum zoom level

# functions
def deg2xy(lat_deg, lon_deg, zoom):
    # returns OSM coordinates (x,y) from (lat,lon) in degree
    # from https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames
    #
    # input: lat_deg = float
    #        long_deg = float
    #        zoom = int
    # output: x = float
    #         y = float

    lat_rad = np.radians(lat_deg)
    n = 2.0**zoom
    x = (lon_deg+180.0)/360.0*n
    y = (1.0-np.arcsinh(np.tan(lat_rad))/np.pi)/2.0*n

    return x, y

def xy2deg(x, y, zoom):
    # returns (lat, lon) in degree from OSM coordinates (x,y)
    # from https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames
    #
    # input: x = float
    #        y = float
    #        zoom = int
    # output: lat_deg = float
    #         lon_deg = float

    n = 2.0**zoom
    lon_deg = x/n*360.0-180.0
    lat_rad = np.arctan(np.sinh(np.pi*(1.0-2.0*y/n)))
    lat_deg = np.degrees(lat_rad)

    return lat_deg, lon_deg

def gaussian_filter(image, sigma):
    # returns image filtered with a gaussian function of variance sigma**2
    #
    # input: image = numpy.ndarray
    #        sigma = float
    # output: image = numpy.ndarray

    i, j = np.meshgrid(np.arange(image.shape[0]), np.arange(image.shape[1]), indexing = 'ij')

    mu = (int(image.shape[0]/2.0), int(image.shape[1]/2.0))

    gaussian = 1.0/(2.0*np.pi*sigma*sigma)*np.exp(-0.5*(((i-mu[0])/sigma)**2+((j-mu[1])/sigma)**2))

    gaussian = np.roll(gaussian, (-mu[0], -mu[1]), axis = (0, 1))

    image_fft = np.fft.rfft2(image)
    gaussian_fft = np.fft.rfft2(gaussian)

    image = np.fft.irfft2(image_fft*gaussian_fft)

    return image

def download_tile(tile_url, tile_file):
    # download tile from url, save to file and wait 0.1s
    #
    # input: tile_url = str
    #        tile_file = str
    # output: bool

    request = urllib.request.Request(tile_url, headers = {'User-Agent':'Mozilla/5.0'})

    try:
        response = urllib.request.urlopen(request)

    except urllib.error.URLError:
        print('ERROR downloading tile from {} failed'.format(tile_url))

        return False

    with open(tile_file, 'wb') as file:
        file.write(response.read())

    time.sleep(0.1)

    return True

def main(args):
    # read GPX trackpoints
    gpx_files = glob.glob('{}/{}'.format(args.dir, args.filter))

    if not gpx_files:
        exit('ERROR no data matching {}/{}'.format(args.dir, args.filter))

    lat_lon_data = []

    for gpx_file in gpx_files:
        print('Reading {}'.format(os.path.basename(gpx_file)))

        with open(gpx_file) as file:
            for line in file:
                if '<time' in line:
                    l = line.split('>')[1][:4]

                    if args.year == 'all' or l in args.year:
                        for line in file:
                            if '<trkpt' in line:
                                l = line.split('"')

                                lat_lon_data.append([float(l[3]), float(l[1])])

                    else:
                        break

    lat_lon_data = np.array(lat_lon_data)

    if lat_lon_data.size == 0:
        exit('ERROR no data matching {}/{}{}'.format(args.dir, args.filter,
                                                     ' with year {}'.format(args.year) if not args.year == 'all' else ''))

    # crop to bounding box
    lat_bound_min, lat_bound_max, lon_bound_min, lon_bound_max = args.bounds

    lat_lon_data = lat_lon_data[np.logical_and(lat_lon_data[:, 0] > lat_bound_min, lat_lon_data[:, 0] < lat_bound_max), :]
    lat_lon_data = lat_lon_data[np.logical_and(lat_lon_data[:, 1] > lon_bound_min, lat_lon_data[:, 1] < lon_bound_max), :]

    if lat_lon_data.size == 0:
        exit('ERROR no data matching {}/{} with bounds {}'.format(args.dir, args.filter, args.bounds))

    print('Read {} trackpoints'.format(lat_lon_data.shape[0]))

    # find tiles coordinates
    lat_min, lon_min = np.min(lat_lon_data, axis = 0)
    lat_max, lon_max = np.max(lat_lon_data, axis = 0)

    if args.zoom > -1:
        zoom = min(args.zoom, OSM_MAX_ZOOM)

        x_tile_min, y_tile_max = map(int, deg2xy(lat_min, lon_min, zoom))
        x_tile_max, y_tile_min = map(int, deg2xy(lat_max, lon_max, zoom))

    else:
        zoom = OSM_MAX_ZOOM

        while True:
            x_tile_min, y_tile_max = map(int, deg2xy(lat_min, lon_min, zoom))
            x_tile_max, y_tile_min = map(int, deg2xy(lat_max, lon_max, zoom))

            if ((x_tile_max-x_tile_min+1)*OSM_TILE_SIZE <= MAX_HEATMAP_SIZE[0] and
                (y_tile_max-y_tile_min+1)*OSM_TILE_SIZE <= MAX_HEATMAP_SIZE[1]):
                break

            zoom -= 1

        print('Auto zoom = {}'.format(zoom))

    tile_count = (x_tile_max-x_tile_min+1)*(y_tile_max-y_tile_min+1)

    if tile_count > MAX_TILE_COUNT:
        exit('ERROR zoom value too high, too many tiles to download')

    # download tiles
    os.makedirs('tiles', exist_ok = True)

    i = 0
    for x in range(x_tile_min, x_tile_max+1):
        for y in range(y_tile_min, y_tile_max+1):
            tile_url = OSM_TILE_SERVER.format(zoom, x, y)

            tile_file = 'tiles/tile_{}_{}_{}.png'.format(zoom, x, y)

            i += 1
            if not glob.glob(tile_file):
                print('downloading tile {}/{}'.format(i, tile_count))

                if not download_tile(tile_url, tile_file):
                    tile_image = np.ones((OSM_TILE_SIZE, OSM_TILE_SIZE, 3))

                    plt.imsave(tile_file, tile_image)

    # create supertile
    supertile = np.zeros(((y_tile_max-y_tile_min+1)*OSM_TILE_SIZE, (x_tile_max-x_tile_min+1)*OSM_TILE_SIZE, 3))

    for x in range(x_tile_min, x_tile_max+1):
        for y in range(y_tile_min, y_tile_max+1):
            tile_file = 'tiles/tile_{}_{}_{}.png'.format(zoom, x, y)

            tile = plt.imread(tile_file)

            i = y-y_tile_min
            j = x-x_tile_min

            supertile[i*OSM_TILE_SIZE:(i+1)*OSM_TILE_SIZE, j*OSM_TILE_SIZE:(j+1)*OSM_TILE_SIZE, :] = tile[:, :, :3]

    if not args.orange:
        supertile = np.sum(supertile*[0.2126, 0.7152, 0.0722], axis = 2) # to grayscale
        supertile = 1.0-supertile # invert colors
        supertile = np.dstack((supertile, supertile, supertile)) # to rgb

    # fill trackpoints
    sigma_pixel = args.sigma if not args.orange else 1

    data = np.zeros(supertile.shape[:2])

    xy_data = deg2xy(lat_lon_data[:, 0], lat_lon_data[:, 1], zoom)

    xy_data = np.array(xy_data).T
    xy_data = np.round((xy_data-[x_tile_min, y_tile_min])*OSM_TILE_SIZE) # to supertile coordinates

    for j, i in xy_data.astype(int):
        data[i-sigma_pixel:i+sigma_pixel, j-sigma_pixel:j+sigma_pixel] += 1.0

    # threshold to max accumulation of trackpoint
    if not args.orange:
        res_pixel = 156543.03*np.cos(np.radians(np.mean(lat_lon_data[:, 0])))/(2.0**zoom) # from https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames

        # trackpoint max accumulation per pixel = 1/5 (trackpoint/meter) * res_pixel (meter/pixel) * activities
        # (Strava records trackpoints every 5 meters in average for cycling activites)
        m = np.round((1.0/5.0)*res_pixel*len(gpx_files))

    else:
        m = 1.0

    data[data > m] = m

    # equalize histogram and compute kernel density estimation
    if not args.orange:
        data_hist, _ = np.histogram(data, bins = int(m+1))

        data_hist = np.cumsum(data_hist)/data.size # normalized cumulated histogram

        for i in range(data.shape[0]):
            for j in range(data.shape[1]):
                data[i, j] = m*data_hist[int(data[i, j])] # histogram equalization

        data = gaussian_filter(data, float(sigma_pixel)) # kernel density estimation with normal kernel

        data = (data-data.min())/(data.max()-data.min()) # normalize to [0,1]

    # colorize
    if not args.orange:
        cmap = plt.get_cmap(PLT_COLORMAP)

        data_color = cmap(data)
        data_color[data_color == cmap(0.0)] = 0.0 # remove background color

        for c in range(3):
            supertile[:, :, c] = (1.0-data_color[:, :, c])*supertile[:, :, c]+data_color[:, :, c]

    else:
        color = np.array([255, 82, 0], dtype = float)/255 # orange

        for c in range(3):
            supertile[:, :, c] = np.minimum(supertile[:, :, c]+gaussian_filter(data, 1.0), 1.0) # white

        data = gaussian_filter(data, 0.5)
        data = (data-data.min())/(data.max()-data.min())

        for c in range(3):
            supertile[:, :, c] = (1.0-data)*supertile[:, :, c]+data*color[c]

    # save image
    plt.imsave(args.output, supertile)

    print('Saved {}'.format(args.output))

    # save csv
    if args.csv and not args.orange:
        csv_file = '{}.csv'.format(os.path.splitext(args.output)[0])

        with open(csv_file, 'w') as file:
            file.write('latitude,longitude,intensity\n') # header

            for i in range(data.shape[0]):
                for j in range(data.shape[1]):
                    if data[i, j] > 0.1:
                        x = x_tile_min+j/OSM_TILE_SIZE
                        y = y_tile_min+i/OSM_TILE_SIZE

                        lat, lon = xy2deg(x, y, zoom)

                        file.write('{},{},{}\n'.format(lat, lon, data[i,j]))

        print('Saved {}'.format(csv_file))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'Generate a PNG heatmap from local Strava GPX files',
                                     epilog = 'Report issues to https://github.com/remisalmon/Strava-local-heatmap/issues')

    parser.add_argument('--dir', default = 'gpx',
                        help = 'GPX files directory  (default: gpx)')
    parser.add_argument('--filter', default = '*.gpx',
                        help = 'GPX files glob filter (default: *.gpx)')
    parser.add_argument('--year', nargs = '+', default = 'all',
                        help = 'GPX files year(s) filter (default: all)')
    parser.add_argument('--bounds', type = float, nargs = 4, metavar = 'BOUND', default = [-90.0, +90.0, -180.0, +180.0],
                        help = 'heatmap bounding box as lat_min, lat_max, lon_min, lon_max (default: -90 +90 -180 +180)')
    parser.add_argument('--output', default = 'heatmap.png',
                        help = 'heatmap name (default: heatmap.png)')
    parser.add_argument('--zoom', type = int, default = -1,
                        help = 'heatmap zoom level 0-19 or -1 for auto (default: -1)')
    parser.add_argument('--sigma', type = int, default = 1,
                        help = 'heatmap Gaussian kernel sigma in pixel (default: 1)')
    parser.add_argument('--orange', action = 'store_true',
                        help = 'not a heatmap...')
    parser.add_argument('--csv', action = 'store_true',
                        help = 'also save the heatmap data to a CSV file')

    args = parser.parse_args()

    main(args)
