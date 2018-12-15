# strava_local_heatmap.py

Python script to reproduce the Strava Global Heatmap ([www.strava.com/heatmap](https://www.strava.com/heatmap)) with local GPX data

Optimized for cycling :bicyclist: activities

## Usage:

* Download your GPX files from Strava and copy them to the `gpx` folder  
(see https://support.strava.com/hc/en-us/articles/216918437-Exporting-your-Data-and-Bulk-Export)
* Run `python3 strava_local_heatmap.py`
* The **heatmap.png** and **heatmap.csv** files are saved in the current directory

### Command-line options:
```
usage: strava_local_heatmap.py [-h] [--gpx-dir DIR] [--gpx-filter FILTER]
                               [--gpx-bound BOUND BOUND BOUND BOUND]
                               [--picture-output PICTURE_FILE]
                               [--csv-output CSV_FILE] [--max-tiles MAXTILES]
                               [--sigma-pixels SIGMA] [--no-cdist]

optional arguments:
  -h, --help            show this help message and exit
  --gpx-dir DIR         directory containing the GPX files (default: gpx)
  --gpx-filter FILTER   regex filter for the GPX files (default: *.gpx)
  --gpx-bound BOUND BOUND BOUND BOUND
                        heatmap bounding box as lat_north_bound,
                        lon_west_bound, lat_south_bound, lon_east_bound
                        (default: 90 -180 -90 180)
  --picture-output PICTURE_FILE
                        heatmap picture file name (default: heatmap.png)
  --csv-output CSV_FILE
                        heatmap CSV data file name (default: heatmap.csv)
  --max-tiles MAXTILES  heatmap maximum dimension in tiles, 1 tile = 256
                        pixels (default: 3)
  --sigma-pixels SIGMA  heatmap Gaussian kernel half-bandwith in pixels
                        (default: 2)
  --no-cdist            disable cumulative distribution of trackpoints
```

Example:  
`strava_local_heatmap.py --gpx-filter *Ride*.gpx --gpx-bound 51.268318 -5.4534286 41.2632185 9.8678344`

## Output:

**heatmap.png:**
![heatmap_zoom.png](images/heatmap_zoom.png)

**heatmap.csv visualization:**  
https://umap.openstreetmap.fr/en/map/demo-heatmap_261644 (contribution by [@badele](https://github.com/badele))

## Installation:

To setup in a Python virtual environment, run `bash setup.sh` (run `deactivate` to exit the virtual environment)

### Python dependencies:
```
python >= 3.7.0
requests >= 2.20.1
matplotlib >= 3.0.2
numpy >= 1.15.4
scipy >= 1.1.0
```
### Other dependencies:

#### Arch Linux:

`sudo pacman -S tk` (cf. https://github.com/remisalmon/strava-local-heatmap/pull/3)

## Projects using strava-local-heatmap.py:

- [JeSuisUnDesDeux](https://gitlab.com/JeSuisUnDesDeux/jesuisundesdeux/tree/master/datas/traces)
