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

# constants
PLT_COLORMAP = 'hot' # matplotlib color map (from https://matplotlib.org/examples/color/colormaps_reference.html)

OSM_TILE_SIZE = 256 # OSM tile size in pixels (do not change)
OSM_MAX_ZOOM = 19 # OSM max zoom level (do not change)

# functions
def deg2num(lat_deg, lon_deg, zoom): # return OSM tile x,y from lat,lon in degrees (from https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames)
  lat_rad = np.radians(lat_deg)
  n = 2.0 ** zoom
  xtile = int((lon_deg + 180.0) / 360.0 * n)
  ytile = int((1.0 - np.log(np.tan(lat_rad) + (1 / np.cos(lat_rad))) / np.pi) / 2.0 * n)

  return(xtile, ytile)

def num2deg(xtile, ytile, zoom): # return lat,lon in degrees from OSM tile x,y (from https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames)
  n = 2.0 ** zoom
  lon_deg = xtile / n * 360.0 - 180.0
  lat_rad = np.arctan(np.sinh(np.pi * (1 - 2 * ytile / n)))
  lat_deg = np.degrees(lat_rad)

  return(lat_deg, lon_deg)

def deg2xy(lat_deg, lon_deg, zoom): # return OSM global x,y coordinates from lat,lon in degrees
    lat_rad = np.radians(lat_deg)
    n = 2.0 ** zoom
    x = (lon_deg + 180.0) / 360.0 * n
    y = (1.0 - np.log(np.tan(lat_rad) + (1 / np.cos(lat_rad))) / np.pi) / 2.0 * n

    return(x, y)

def box_filter(image, w_box): # return image filtered with box filter
    box = np.ones((w_box, w_box))/(w_box**2)

    image_fft = np.fft.rfft2(image)
    box_fft = np.fft.rfft2(box, s = image.shape)

    image = np.fft.irfft2(image_fft*box_fft)

    return(image)

def download_tile(tile_url, tile_file): # download image from url to file
    request = urllib.request.Request(url = tile_url, data = None, headers = {'User-Agent':'Mozilla/5.0'})

    try:
        response = urllib.request.urlopen(request)
    except urllib.error.URLError as e: # (from https://docs.python.org/3/howto/urllib2.html)
        print('ERROR cannot download tile from OSM server')

        if hasattr(e, 'reason'):
            print(e.reason)

        elif hasattr(e, 'code'):
            print(e.code)

        status = False
    else:
        with open(tile_file, 'wb') as file:
            file.write(response.read())

        time.sleep(0.1)

        status = True

    return(status)

def main(args):
    # parameters
    gpx_dir = args.dir # string
    gpx_glob = args.glob # string
    gpx_year = args.year # string
    lat_bound_min, lat_bound_max, lon_bound_min, lon_bound_max = args.bound # int
    heatmap_file = args.file # string
    heatmap_scale = args.scale # int
    sigma_pixels = args.sigma # int
    use_csv = args.csv # bool
    use_cumululative_distribution = not args.nocdist # bool

    zoom = OSM_MAX_ZOOM

    try:
        cmap = plt.get_cmap(PLT_COLORMAP)
    except:
        print('ERROR colormap '+PLT_COLORMAP+' does not exists')
        quit()

    # find GPX files
    gpx_files = glob.glob(gpx_dir+'/'+gpx_glob)

    if not gpx_files:
        print('ERROR no data matching '+gpx_dir+'/'+gpx_glob)
        quit()

    # read GPX files
    lat_lon_data = [] # initialize latitude, longitude list

    for i in range(len(gpx_files)):
        print('reading GPX file '+str(i+1)+'/'+str(len(gpx_files))+'...')

        with open(gpx_files[i]) as file:
            for line in file:
                if '<time' in line: # activity date
                    tmp = re.findall('\d{4}', line)

                    if gpx_year in (tmp[0], 'all'):
                        for line in file:
                            if '<trkpt' in line: # trackpoints latitude, longitude
                                tmp = re.findall('-?\d*\.?\d+', line)

                                lat_lon_data.append([float(tmp[0]), float(tmp[1])])
                    else:
                        break

    if not lat_lon_data:
        print('ERROR no data matching '+gpx_dir+'/'+gpx_glob+' with --gpx-year '+gpx_year)
        quit()

    print('processing GPX data...')

    lat_lon_data = np.array(lat_lon_data) # convert list to NumPy array

    # crop data to bounding box
    lat_lon_data = lat_lon_data[np.logical_and(lat_lon_data[:, 0] > lat_bound_min, lat_lon_data[:, 0] < lat_bound_max), :]
    lat_lon_data = lat_lon_data[np.logical_and(lat_lon_data[:, 1] > lon_bound_min, lat_lon_data[:, 1] < lon_bound_max), :]

    if lat_lon_data.size == 0:
        print('ERROR no matching '+gpx_dir+'/'+gpx_glob+' with --gpx-bound '+' '.join(str(s) for s in [lat_bound_min, lat_bound_max, lon_bound_min, lon_bound_max]))
        quit()

    # find good zoom level to match max_nb_tiles
    lat_min = lat_lon_data[:, 0].min()
    lat_max = lat_lon_data[:, 0].max()
    lon_min = lat_lon_data[:, 1].min()
    lon_max = lat_lon_data[:, 1].max()

    while True:
        x_tile_min, y_tile_max = deg2num(lat_min, lon_min, zoom)
        x_tile_max, y_tile_min = deg2num(lat_max, lon_max, zoom)

        if max(x_tile_max-x_tile_min+1, y_tile_max-y_tile_min+1) > heatmap_scale: # decrease zoom level if number of tiles used is too high
            zoom -= 1

        else:
            break

    tile_count = (x_tile_max-x_tile_min+1)*(y_tile_max-y_tile_min+1) # total number of tiles

    # download tiles
    if not os.path.exists('tiles'):
        os.makedirs('tiles')

    i = 0
    for x in range(x_tile_min, x_tile_max+1):
        for y in range(y_tile_min, y_tile_max+1):
            tile_url = 'https://maps.wikimedia.org/osm-intl/'+str(zoom)+'/'+str(x)+'/'+str(y)+'.png' # (from https://wiki.openstreetmap.org/wiki/Tile_servers)

            tile_file = 'tiles/tile_'+str(zoom)+'_'+str(x)+'_'+str(y)+'.png'

            if not glob.glob(tile_file): # check if tile already downloaded
                i += 1

                print('downloading tile '+str(i)+'/'+str(tile_count)+'...')

                if not download_tile(tile_url, tile_file):
                    tile_image = np.ones((OSM_TILE_SIZE, OSM_TILE_SIZE, 3))

                    plt.imsave(tile_file, tile_image)

    print('creating heatmap...')

    # create supertile
    supertile_size = ((y_tile_max-y_tile_min+1)*OSM_TILE_SIZE, (x_tile_max-x_tile_min+1)*OSM_TILE_SIZE, 3)

    supertile = np.zeros(supertile_size)

    for x in range(x_tile_min, x_tile_max+1):
        for y in range(y_tile_min, y_tile_max+1):
            tile_filename = 'tiles/tile_'+str(zoom)+'_'+str(x)+'_'+str(y)+'.png'

            tile = plt.imread(tile_filename) # float ([0,1])

            i = y-y_tile_min
            j = x-x_tile_min

            supertile[i*OSM_TILE_SIZE:i*OSM_TILE_SIZE+OSM_TILE_SIZE, j*OSM_TILE_SIZE:j*OSM_TILE_SIZE+OSM_TILE_SIZE, :] = tile[:, :, :3] # fill supertile with tile image

    # convert supertile to grayscale and invert colors
    supertile = 0.2126*supertile[:, :, 0]+0.7152*supertile[:, :, 1]+0.0722*supertile[:, :, 2] # convert to 1 channel grayscale image

    supertile = 1-supertile # invert colors

    supertile = np.dstack((supertile, supertile, supertile)) # convert back to 3 channels image

    # fill trackpoints data
    data = np.zeros(supertile_size[:2])

    w_pixels = int(sigma_pixels) # add w_pixels (= Gaussian kernel sigma) pixels of padding around the trackpoints for better visualization

    for k in range(len(lat_lon_data)):
        x, y = deg2xy(lat_lon_data[k, 0], lat_lon_data[k, 1], zoom)

        i = int(np.round((y-y_tile_min)*OSM_TILE_SIZE))
        j = int(np.round((x-x_tile_min)*OSM_TILE_SIZE))

        data[i-w_pixels:i+w_pixels+1, j-w_pixels:j+w_pixels+1] += 1 # ensure pixels are centered on the trackpoint

    # threshold trackpoints accumulation to avoid large local maxima
    if use_cumululative_distribution:
        pixel_res = 156543.03*np.cos(np.radians(np.mean(lat_lon_data[:, 0])))/(2**zoom) # pixel resolution (from https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames)

        m = (1.0/5.0)*pixel_res*len(gpx_files) # trackpoints max accumulation per pixel = (1/5) trackpoints/meters * (pixel_res) meters/pixels per (1) activity (Strava records trackpoints every 5 meters in average for cycling activites)
    else:
        m = 1.0

    data[data > m] = m # threshold data to maximum accumulation of trackpoints

    # kernel density estimation = convolution with (almost-)Gaussian kernel
    w_filter = int(np.sqrt(12.0*sigma_pixels**2+1.0)) # (from https://www.peterkovesi.com/papers/FastGaussianSmoothing.pdf)

    data = box_filter(data, w_filter)

    # normalize data to [0,1]
    data = (data-data.min())/(data.max()-data.min())

    # colorize data
    data_color = cmap(data)

    data_color[(data_color == cmap(0)).all(2)] = [0.0, 0.0, 0.0, 1.0] # remove background color

    data_color = data_color[:, :, :3] # remove alpha channel

    # create color overlay
    supertile_overlay = np.zeros(supertile_size)

    for c in range(3):
        supertile_overlay[:, :, c] = (1.0-data_color[:, :, c])*supertile[:, :, c]+data_color[:, :, c] # fill color overlay

    # save image
    if not os.path.splitext(heatmap_file)[1] == '.png': # make sure we use PNG
        heatmap_file = os.path.splitext(heatmap_file)[0]+'.png'

    print('saving '+heatmap_file+'...')

    plt.imsave(heatmap_file, supertile_overlay)

    # save csv file
    if use_csv:
        csv_file = os.path.splitext(heatmap_file)[0]+'.csv'

        print('saving '+csv_file+'...')

        with open(csv_file, 'w') as file:
            file.write('lat,lon,intensity\n')

            for i in range(data.shape[0]):
                for j in range(data.shape[1]):
                    if data[i, j] > 0.1:
                        x = x_tile_min+j/OSM_TILE_SIZE
                        y = y_tile_min+i/OSM_TILE_SIZE

                        lat, lon = num2deg(x, y, zoom)

                        file.write(str(lat)+','+str(lon)+','+str(data[i, j])+'\n')

    print('done')

if __name__ == '__main__':
    # command line parameters
    parser = argparse.ArgumentParser(description = 'Generate a local heatmap from Strava GPX files', epilog = 'Report issues to https://github.com/remisalmon/strava-local-heatmap')

    parser.add_argument('--gpx-dir', dest = 'dir', default = 'gpx', help = 'GPX files directory  (default: gpx)')
    parser.add_argument('--gpx-filter', dest = 'glob', default = '*.gpx', help = 'GPX files glob filter (default: *.gpx)')
    parser.add_argument('--gpx-year', dest = 'year', default = 'all', help = 'GPX files year filter (default: all)')
    parser.add_argument('--gpx-bound', dest = 'bound', type = float, nargs = 4, default = [-90, +90, -180, +180], help = 'heatmap bounding box coordinates as lat_min, lat_max, lon_min, lon_max (default: -90 +90 -180 +180)')
    parser.add_argument('--output', dest = 'file', default = 'heatmap.png', help = 'heatmap name (default: heatmap.png)')
    parser.add_argument('--csv', dest = 'csv', action = 'store_true', help = 'also save the heatmap data to a CSV file')
    parser.add_argument('--scale', dest = 'scale', type = int, default = 3, help = 'heatmap size in multiples of 256 (default: 3)')
    parser.add_argument('--bandwith', dest = 'sigma', type = int, default = 1, help = 'heatmap Gaussian kernel bandwith in pixels (default: 1)')
    parser.add_argument('--no-cdist', dest = 'nocdist', action = 'store_true', help = 'disable cumulative distribution of trackpoints (uniform distribution)')

    args = parser.parse_args()

    # run main
    main(args)
