# strava_local_heatmap.py

Python script to reproduce the Strava Global Heatmap ([www.strava.com/heatmap](https://www.strava.com/heatmap)) with local GPX data

For an interactive version, check out [github.com/remisalmon/Strava-local-heatmap-browser](https://github.com/remisalmon/Strava-local-heatmap-browser)

Optimized for cycling activities :bicyclist:

## Features

* Minimal Python dependencies (matplotlib+numpy)
* Fast (3x faster than `gpxpy.parse()`)

## Usage

* Download your GPX files from Strava and add them to the `gpx` folder  
(see https://support.strava.com/hc/en-us/articles/216918437-Exporting-your-Data-and-Bulk-Export)
* Run `python3 strava_local_heatmap.py`
* The **heatmap.png** image is saved to the current directory

### Command-line options

```
usage: strava_local_heatmap.py [-h] [--gpx-dir DIR] [--gpx-filter GLOB]
                               [--gpx-year YEAR]
                               [--gpx-bound BOUND BOUND BOUND BOUND]
                               [--output FILE] [--csv] [--scale SCALE]
                               [--bandwith SIGMA] [--no-cdist]

optional arguments:
  -h, --help            show this help message and exit
  --gpx-dir DIR         GPX files directory (default: gpx)
  --gpx-filter GLOB     GPX files glob filter (default: *.gpx)
  --gpx-year YEAR       GPX files year filter (default: all)
  --gpx-bound BOUND BOUND BOUND BOUND
                        heatmap bounding box coordinates as lat_min, lat_max,
                        lon_min, lon_max (default: -90 +90 -180 +180)
  --output FILE         heatmap name (default: heatmap.png)
  --csv                 also save the heatmap data to a CSV file
  --scale SCALE         heatmap size in multiples of 256 (default: 3)
  --bandwith SIGMA      heatmap Gaussian kernel bandwith in pixels (default:
                        1)
  --no-cdist            disable cumulative distribution of trackpoints
                        (uniform distribution)
```

Example:  
`strava_local_heatmap.py --gpx-filter *Ride*.gpx --gpx-year 2018 --gpx-bound 24.39 49.38 -124.84-66.88`

For an explanation on the cumulative distribution function, see:  
https://medium.com/strava-engineering/the-global-heatmap-now-6x-hotter-23fc01d301de

## Output

**heatmap.png**  
![heatmap_zoom.png](output_heatmap.png)

**heatmap.csv**  
See https://umap.openstreetmap.fr/en/map/demo-heatmap_261644 (contribution by [@badele](https://github.com/badele))

## Installation

To setup in a local Python virtual environment, run `setup.sh`

To activate the virtual environment, run `source virtualenv/bin/activate`

### Python dependencies

```
matplotlib==3.0.2
numpy==1.15.4
```

### Other dependencies

Arch Linux (see [here](https://github.com/remisalmon/strava-local-heatmap/pull/3#issuecomment-443541311)): `sudo pacman -S tk`

## Projects using strava_local_heatmap.py

- [JeSuisUnDesDeux](https://gitlab.com/JeSuisUnDesDeux/jesuisundesdeux/tree/master/datas/traces)
