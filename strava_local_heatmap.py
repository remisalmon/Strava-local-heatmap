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

https://www.findlatitudeandlongitude.com/
"""

#%% librairies
import os
import glob
import time
import re
import requests
import math
import matplotlib
import numpy

import skimage.color
import skimage.filters
import skimage.io

#%% functions

# return OSM x,y tile ID from lat,lon in degrees
def deg2num(lat_deg, lon_deg, zoom):
  lat_rad = math.radians(lat_deg)
  n = 2.0 ** zoom
  xtile = int((lon_deg + 180.0) / 360.0 * n)
  ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
  return(xtile, ytile)

# return x,y coordinates in tile from lat,lon in degrees
def deg2xy(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    x = (lon_deg + 180.0) / 360.0 * n
    y = (1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n
    return(x, y)

# download image
def downloadtile(url, filename):
    req = requests.get(url)
    with open(filename, 'wb') as file:
        for chunk in req.iter_content(chunk_size = 256):
            file.write(chunk)
            file.flush()
    time.sleep(0.1)
    return

#%% parameters
tile_size = [256, 256] # OSM tile size (default)
zoom = 19 # OSM max zoom level (default)

sigma_pixels = 1.5 # Gaussian kernel sigma (half bandwith, in pixels)

colormap_style = 'hot' # heatmap color map, from matplotlib

#%% main

# find gpx file
gpx_files = glob.glob('./gpx/*.gpx')

if not gpx_files:
    print('ERROR: no GPX files in ./gpx/')
    quit()

# initialize list
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

# convert to NumPy array
lat_lon_data = numpy.array(lat_lon_data)

print('processing GPX data...')

# find good zoom level and corresponding OSM tiles x,y
xy_tiles = numpy.zeros(lat_lon_data.shape, dtype = int)

while True: # replace with check on lat, lon min, max
    for i in range(len(xy_tiles)):
        xy_tiles[i, :] = deg2num(lat_lon_data[i, 0], lat_lon_data[i, 1], zoom)

    # find bounding OSM x,y tiles ID
    x_tile_min = min(xy_tiles[:, 0])
    x_tile_max = max(xy_tiles[:, 0])
    y_tile_min = min(xy_tiles[:, 1])
    y_tile_max = max(xy_tiles[:, 1])

    # check area size
    tile_count = (x_tile_max-x_tile_min+1)*(y_tile_max-y_tile_min+1)
    
    if (x_tile_max-x_tile_min+1) > 6 or (y_tile_max-y_tile_min+1) > 6:
        zoom = zoom-1
    else:
        break

# download tiles
if not os.path.exists('./tiles'):
	os.mkdir('./tiles')

i = 0
for x in range(x_tile_min, x_tile_max+1):
    for y in range(y_tile_min, y_tile_max+1):
        tile_url = 'https://maps.wikimedia.org/osm-intl/'+str(zoom)+'/'+str(x)+'/'+str(y)+'.png'
        tile_filename = './tiles/tile_'+str(zoom)+'_'+str(x)+'_'+str(y)+'.png'
        
        if not glob.glob(tile_filename):
            i = i+1
            print('downloading tile '+str(i)+'/'+str(tile_count)+'...')
            
            downloadtile(tile_url, tile_filename)

print('creating heatmap...')

# create supertile
supertile_size = [(y_tile_max-y_tile_min+1)*tile_size[0], (x_tile_max-x_tile_min+1)*tile_size[1], 3]

supertile = numpy.zeros(supertile_size)
supertile_gray = numpy.zeros(supertile_size[0:2])

# read tiles and fill supertile
for x in range(x_tile_min, x_tile_max+1):
    for y in range(y_tile_min, y_tile_max+1):
        tile_filename = 'tiles/tile_'+str(zoom)+'_'+str(x)+'_'+str(y)+'.png'
        
        tile = skimage.io.imread(tile_filename) # uint8 data type
        
        tile = skimage.color.rgb2gray(tile) # OSM tiles have either 1 or 3 channels..., reduce to 1 by default
        tile = skimage.img_as_float(tile) # convert uint8 to float
        
        i = y-y_tile_min
        j = x-x_tile_min
        
        supertile_gray[i*tile_size[0]:i*tile_size[0]+tile_size[0], j*tile_size[1]:j*tile_size[1]+tile_size[1]] = tile
        
# convert supertile to 3 channels image for coloring
supertile = skimage.color.gray2rgb(supertile_gray)

# invert supertile colors
supertile = 1-supertile

# fill trackpoints data
data = numpy.zeros(supertile_size[0:2])

for k in range(len(lat_lon_data)):
    (x, y) = deg2xy(lat_lon_data[k, 0], lat_lon_data[k, 1], zoom)
    
    i = int(numpy.round((y-y_tile_min)*tile_size[0]))
    j = int(numpy.round((x-x_tile_min)*tile_size[1]))
    
    data[i-1:i+1, j-1:j+1] = data[i-1:i+1, j-1:j+1] + 1 # GPX trackpoint is 3x3 pixels

# trim data accumulation to maximum number of activities
data[data > len(gpx_files)*2] = len(gpx_files)*2 # assuming each activity goes through the same trackpoints 2 times at most

# kernel density estimation = convolution with Gaussian kernel + normalization
data = skimage.filters.gaussian(data, sigma_pixels)

data = (data-data.min())/(data.max()-data.min())

# colorize data
cmap = matplotlib.pyplot.get_cmap(colormap_style)

data_color = cmap(data)
data_color = data_color-cmap(0) # remove background color
data_color = data_color[:, :, 0:3] # remove alpha channel

# create color overlay
supertile_overlay = numpy.zeros(supertile_size)

# fill color overlay
for c in range(3):    
    supertile_overlay[:, :, c] = (1-data_color[:, :, c])*supertile[:, :, c]+data_color[:, :, c]

# crop values out of range [0,1]
supertile_overlay = numpy.minimum.reduce([supertile_overlay, numpy.ones(supertile_size)])
supertile_overlay = numpy.maximum.reduce([supertile_overlay, numpy.zeros(supertile_size)])

# save image
print('saving heatmap.png...')

skimage.io.imsave('heatmap.png', supertile_overlay)

print('done')
