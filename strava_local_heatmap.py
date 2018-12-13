"""
Remi Salmon
salmon.remi@gmail.com

November 17, 2017

References:
https://support.strava.com/hc/en-us/articles/216918437-Exporting-your-Data-and-Bulk-Export

http://wiki.openstreetmap.org/wiki/Slippy_map_tilenames
http://wiki.openstreetmap.org/wiki/Tile_servers

http://matplotlib.org/examples/color/colormaps_reference.html

http://scikit-image.org/
"""

# librairies
import os
import glob
import time
import re
import argparse
import requests

import numpy as np
import matplotlib.pyplot as plt

import skimage.filters

# functions
def deg2num(lat_deg, lon_deg, zoom): # return OSM x,y tile ID from lat,lon in degrees (from http://wiki.openstreetmap.org/wiki/Slippy_map_tilenames)
  lat_rad = np.radians(lat_deg)
  n = 2.0 ** zoom
  xtile = int((lon_deg + 180.0) / 360.0 * n)
  ytile = int((1.0 - np.log(np.tan(lat_rad) + (1 / np.cos(lat_rad))) / np.pi) / 2.0 * n)
  return(xtile, ytile)

def deg2xy(lat_deg, lon_deg, zoom): # return x,y coordinates in tile from lat,lon in degrees
    lat_rad = np.radians(lat_deg)
    n = 2.0 ** zoom
    x = (lon_deg + 180.0) / 360.0 * n
    y = (1.0 - np.log(np.tan(lat_rad) + (1 / np.cos(lat_rad))) / np.pi) / 2.0 * n
    return(x, y)

def xy2deg(xtile, ytile, zoom): # return x,y coordinates in tile from lat,lon in degrees (from http://wiki.openstreetmap.org/wiki/Slippy_map_tilenames)
  n = 2.0 ** zoom
  lon_deg = xtile / n * 360.0 - 180.0
  lat_rad = np.arctan(np.sinh(np.pi * (1 - 2 * ytile / n)))
  lat_deg = np.degrees(lat_rad)
  return (lat_deg, lon_deg)

def downloadtile(url, filename): # download tile image
    req = requests.get(url)
    with open(filename, 'wb') as file:
        for chunk in req.iter_content(chunk_size = 256):
            file.write(chunk)
            file.flush()
    time.sleep(0.1)
    return

# main script

# Analyze command line parameters
ap = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
ap.add_argument("-g", "--gpx",default="./gpx",
	help="GPX folder")
ap.add_argument("-f", "--filter",default="*.gpx",
	help="Filename filter")
ap.add_argument("-p", "--picture-output",default="heatmap.png",
	help="Picture output")
ap.add_argument("-d", "--data-output",default="heatmap.csv",
	help="Data CSV output")

ap.add_argument("-c", "--colormap",default="hot",
	help="heatmap color map (from http://matplotlib.org/examples/color/colormaps_reference.html)")
ap.add_argument("-a", "--accumulation-distribution",default=True, type=lambda x: (str(x).lower() == 'true'),
	help="Take into account the accumulation of trackpoints in each pixel")
ap.add_argument("-s", "--sigma-pixels",type=int,default=2,
	help="Gaussian kernel sigma (half-bandwith in pixels)")
ap.add_argument("-t", "--tile-size",default=[256, 256],
	help="OSM tile size")
ap.add_argument("-m", "--max-nb-tiles",type=int,default=5,
	help="Maximum number of OSM tiles to construct the heatmap (heatmap max dimension is max_nb_tiles*256)")
ap.add_argument("-z", "--max-zoom",type=int,default=19,
	help="OSM max zoom level")
ap.add_argument("-b", "--limit-bounds",nargs=4,type=float,default=[+90, -180, -90, +180],
	help="Set lat, lon boundaries +90 -180 -90 +180 to keep all trackpoints)")

args = vars(ap.parse_args())

#%% parameters
max_nb_tiles = args["max_nb_tiles"]
use_cumululative_distribution =  args["accumulation_distribution"]
sigma_pixels = args["sigma_pixels"]
colormap_style = args["colormap"]
tile_size = args["tile_size"]
zoom = args["max_zoom"]
lat_north_bound, lon_west_bound, lat_south_bound, lon_east_bound  = args["limit_bounds"]
picture_output = args["picture_output"]
data_output = args["data_output"]
gpxfolder = args["gpx"]
gpxfilter = args["filter"]

# find gpx file
gpx_files = glob.glob('%(gpxfolder)s/%(gpxfilter)s' % locals(),recursive=True)

if not gpx_files:
    print('ERROR: no GPX files in gpx folder')
    quit()

# initialize latitude, longitude list
lat_lon_data = []

# read GPX files
for i in range(len(gpx_files)):
    print('reading GPX file '+str(i+1)+'/'+str(len(gpx_files))+'...')

    with open(gpx_files[i]) as file:
        for line in file:
            # get trackpoints latitude, longitude
            if '<trkpt' in line:
                tmp = re.findall('-?\d*\.?\d+', line)

                lat = float(tmp[0])
                lon = float(tmp[1])

                lat_lon_data.append([lat, lon])

print('processing GPX data...')

lat_lon_data = np.array(lat_lon_data) # convert to NumPy array

# crop data to bounding box
lat_lon_data = lat_lon_data[np.logical_and(lat_lon_data[:, 0] > lat_south_bound, lat_lon_data[:, 0] < lat_north_bound), :]
lat_lon_data = lat_lon_data[np.logical_and(lat_lon_data[:, 1] > lon_west_bound, lat_lon_data[:, 1] < lon_east_bound), :]

# find good zoom level and corresponding OSM tiles x,y
xy_tiles_minmax = np.zeros((4, 2), dtype = int)

lat_min = lat_lon_data[:, 0].min()
lat_max = lat_lon_data[:, 0].max()
lon_min = lat_lon_data[:, 1].min()
lon_max = lat_lon_data[:, 1].max()
while True:
    # find x,y tiles coordinates of bounding box
    xy_tiles_minmax[0, :] = deg2num(lat_min, lon_min, zoom)
    xy_tiles_minmax[1, :] = deg2num(lat_min, lon_max, zoom)
    xy_tiles_minmax[2, :] = deg2num(lat_max, lon_min, zoom)
    xy_tiles_minmax[3, :] = deg2num(lat_max, lon_max, zoom)

    x_tile_min = xy_tiles_minmax[:, 0].min()
    x_tile_max = xy_tiles_minmax[:, 0].max()
    y_tile_min = xy_tiles_minmax[:, 1].min()
    y_tile_max = xy_tiles_minmax[:, 1].max()

    # decrease zoom level if number of tiles used is too high
    if (x_tile_max-x_tile_min+1) > max_nb_tiles or (y_tile_max-y_tile_min+1) > max_nb_tiles:
        zoom = zoom-1
    else:
        break

tile_count = (x_tile_max-x_tile_min+1)*(y_tile_max-y_tile_min+1) # total number of tiles

# download tiles
if not os.path.exists('./tiles'):
    os.mkdir('./tiles')

i = 0
for x in range(x_tile_min, x_tile_max+1):
    for y in range(y_tile_min, y_tile_max+1):
        tile_url = 'https://maps.wikimedia.org/osm-intl/'+str(zoom)+'/'+str(x)+'/'+str(y)+'.png' # (from http://wiki.openstreetmap.org/wiki/Tile_servers)
        tile_filename = './tiles/tile_'+str(zoom)+'_'+str(x)+'_'+str(y)+'.png'

        if not glob.glob(tile_filename):
            i = i+1
            print('downloading tile '+str(i)+'/'+str(tile_count)+'...')

            downloadtile(tile_url, tile_filename)

print('creating heatmap...')

# create supertile
supertile_size = [(y_tile_max-y_tile_min+1)*tile_size[0], (x_tile_max-x_tile_min+1)*tile_size[1], 3]

supertile = np.zeros(supertile_size)

for x in range(x_tile_min, x_tile_max+1):
    for y in range(y_tile_min, y_tile_max+1):
        tile_filename = 'tiles/tile_'+str(zoom)+'_'+str(x)+'_'+str(y)+'.png'

        tile = plt.imread(tile_filename) # float32 data type [0,1]

        i = y-y_tile_min
        j = x-x_tile_min

        supertile[i*tile_size[0]:i*tile_size[0]+tile_size[0], j*tile_size[1]:j*tile_size[1]+tile_size[1], :] = tile # fill supertile with tile image

# convert supertile to grayscale and invert colors
supertile = 0.2126*supertile[:, :, 0]+0.7152*supertile[:, :, 1]+0.0722*supertile[:, :, 2] # convert to 1 channel grayscale image
supertile = 1-supertile
supertile = np.dstack((supertile, supertile, supertile)) # convert back to 3 channels image

# fill trackpoints data
data = np.zeros(supertile_size[0:2])

w_pixels = int(sigma_pixels) # add w_pixels ( = Gaussian kernel sigma) pixels of padding around the trackpoints for better visualization (data point size in pixels = 2*w_pixels+1)

for k in range(len(lat_lon_data)):
    (x, y) = deg2xy(lat_lon_data[k, 0], lat_lon_data[k, 1], zoom)

    i = int(np.round((y-y_tile_min)*tile_size[0]))
    j = int(np.round((x-x_tile_min)*tile_size[1]))

    data[i-w_pixels:i+w_pixels+1, j-w_pixels:j+w_pixels+1] = data[i-w_pixels:i+w_pixels+1, j-w_pixels:j+w_pixels+1] + 1 # ensure pixels are centered on the trackpoint

# threshold trackpoints accumulation to avoid large local maxima
if use_cumululative_distribution:
    pixel_res = 156543.03*np.cos(np.radians(lat_lon_data[:, 0].mean()))/(2**zoom) # pixel resolution (from https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames)

    m = (1.0/5.0)*pixel_res*len(gpx_files) # trackpoints max accumulation per pixel = (1/5) trackpoints/meters * (pixel_res) meters/pixels per (1) activity (Strava records trackpoints every 5 meters in average)
else:
    m = 1.0

data[data > m] = m # threshold data to maximum accumulation of trackpoints

# kernel density estimation = convolution with Gaussian kernel
data = skimage.filters.gaussian(data, sigma_pixels)

# normalize data to [0,1]
data = (data-data.min())/(data.max()-data.min())

# colorize data
cmap = plt.get_cmap(colormap_style)

data_color = cmap(data)
data_color[(data_color == cmap(0)).all(2)] = [0.0, 0.0, 0.0, 1.0] # remove background color
data_color = data_color[:, :, 0:3] # remove alpha channel

# create color overlay
supertile_overlay = np.zeros(supertile_size)

for c in range(3):
    supertile_overlay[:, :, c] = (1-data_color[:, :, c])*supertile[:, :, c]+data_color[:, :, c] # fill color overlay

# save image
print('saving %(picture_output)s ...' % locals())

plt.imsave('%(picture_output)s' % locals(), supertile_overlay)

# save csv file
print('saving %(data_output)s  ...' % locals())

with open('%(data_output)s' % locals(), 'w') as file:
    file.write('lat,lon,intensity\n')

    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            if data[i, j] > 0.1:
                x = x_tile_min+j/tile_size[1]
                y = y_tile_min+i/tile_size[0]

                (lat, lon) = xy2deg(x, y, zoom)

                file.write(str(lat)+','+str(lon)+','+str(data[i, j])+'\n')

print('done')
