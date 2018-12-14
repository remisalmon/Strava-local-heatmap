# strava_local_heatmap.py

Python script to reproduce the Strava Global Heatmap ([www.strava.com/heatmap](https://www.strava.com/heatmap)) with local GPX data

## Usage:

* Download your GPX files from Strava to the `gpx` folder (see https://support.strava.com/hc/en-us/articles/216918437-Exporting-your-Data-and-Bulk-Export)
* [Optional] Edit the parameters in `strava_local_heatmap.py`:  
`max_nb_tiles` to change the heatmap resolution  
`lat_north_bound,lon_west_bound,lat_south_bound,lon_east_bound` to change the heatmap region (bounding box)
* Run `python3 strava_local_heatmap.py`
* The **heatmap.png** and **heatmap.csv** files are saved to the current directory

```
Example for sub directories GPX datas with bounds limit
python strava_local_heatmap.py -g ~/jesuisundesdeux/datas/traces -f "**/*_reduced_trace.gpx" -b 43.629366 3.835258 43.576101 3.975334

usage: strava_local_heatmap.py [-h] [-g GPX] [-f FILTER] [-p PICTURE_OUTPUT]
                               [-d DATA_OUTPUT] [-c COLORMAP]
                               [-a ACCUMULATION_DISTRIBUTION]
                               [-s SIGMA_PIXELS] [-t TILE_SIZE]
                               [-m MAX_NB_TILES] [-z MAX_ZOOM]
                               [-b LIMIT_BOUNDS LIMIT_BOUNDS LIMIT_BOUNDS LIMIT_BOUNDS]

optional arguments:
  -h, --help            show this help message and exit
  -g GPX, --gpx GPX     GPX folder (default: ./gpx)
  -f FILTER, --filter FILTER
                        Filename filter (default: *.gpx)
  -p PICTURE_OUTPUT, --picture-output PICTURE_OUTPUT
                        Picture output (default: heatmap.png)
  -d DATA_OUTPUT, --data-output DATA_OUTPUT
                        Data CSV output (default: heatmap.csv)
  -c COLORMAP, --colormap COLORMAP
                        heatmap color map (from http://matplotlib.org/examples
                        /color/colormaps_reference.html) (default: hot)
  -a ACCUMULATION_DISTRIBUTION, --accumulation-distribution ACCUMULATION_DISTRIBUTION
                        Take into account the accumulation of trackpoints in
                        each pixel (default: True)
  -s SIGMA_PIXELS, --sigma-pixels SIGMA_PIXELS
                        Gaussian kernel sigma (half-bandwith in pixels)
                        (default: 2)
  -t TILE_SIZE, --tile-size TILE_SIZE
                        OSM tile size (default: [256, 256])
  -m MAX_NB_TILES, --max-nb-tiles MAX_NB_TILES
                        Maximum number of OSM tiles to construct the heatmap
                        (heatmap max dimension is max_nb_tiles*256) (default:
                        5)
  -z MAX_ZOOM, --max-zoom MAX_ZOOM
                        OSM max zoom level (default: 19)
  -b LIMIT_BOUNDS LIMIT_BOUNDS LIMIT_BOUNDS LIMIT_BOUNDS, --limit-bounds LIMIT_BOUNDS LIMIT_BOUNDS LIMIT_BOUNDS LIMIT_BOUNDS
                        Set lat, lon boundaries +90 -180 -90 +180 to keep all
                        trackpoints) (default: [90, -180, -90, 180])

```

**heatmap.png:**
![heatmap_zoom.png](images/heatmap_zoom.png)

**heatmap.csv visualization:**  
https://umap.openstreetmap.fr/en/map/demo-heatmap_261644 (contribution by [@badele](https://github.com/badele))

## Python dependencies:

* python >= 3.7.0
* requests >= 2.20.1
* numpy >= 1.15.4
* matplotlib >= 3.0.2
* scikit-image >= 0.14.1 (https://scikit-image.org/)

To setup in a Python virtual environment, run `bash setup.sh` (run `deactivate` to exit the virtual environment)

## Distribution dependencies:

### Arch Linux

`sudo pacman -S tk` (cf. https://github.com/remisalmon/strava-local-heatmap/pull/3)

## Projects use strava-local-heatmap

- [JeSuisUnDesDeux](https://gitlab.com/JeSuisUnDesDeux/jesuisundesdeux/tree/master/datas/traces)