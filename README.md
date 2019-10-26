# strava_local_heatmap.py

Python script to reproduce the Strava Global Heatmap ([www.strava.com/heatmap](https://www.strava.com/heatmap)) with local GPX data

Optimized for cycling activities :bicyclist:

**Check out [github.com/remisalmon/Strava-local-heatmap-browser](https://github.com/remisalmon/Strava-local-heatmap-browser) for an interactive version**

## Features

* Minimal Python dependencies (matplotlib+numpy)
* Fast (3x faster than `gpxpy.parse()`)

## Usage

* Download your GPX files from Strava and add them to the `gpx` folder  
(see https://support.strava.com/hc/en-us/articles/216918437-Exporting-your-Data-and-Bulk-Export)
* Run `python3 strava_local_heatmap.py`
* The heatmap is saved to `heatmap.png`

### Command-line options

```
usage: strava_local_heatmap.py [-h] [--gpx-dir DIR] [--gpx-year YEAR]
                               [--gpx-filter GLOB]
                               [--gpx-bound BOUND BOUND BOUND BOUND]
                               [--output FILE] [--zoom ZOOM] [--sigma SIGMA]
                               [--no-cdist] [--csv]

optional arguments:
  -h, --help            show this help message and exit
  --gpx-dir DIR         GPX files directory (default: gpx)
  --gpx-year YEAR       GPX files year filter (default: all)
  --gpx-filter GLOB     GPX files glob filter (default: *.gpx)
  --gpx-bound BOUND BOUND BOUND BOUND
                        heatmap bounding box coordinates as lat_min, lat_max,
                        lon_min, lon_max (default: -90 +90 -180 +180)
  --output FILE         heatmap name (default: heatmap.png)
  --zoom ZOOM           heatmap zoom level 0-19 (default: 10)
  --sigma SIGMA         heatmap Gaussian kernel sigma in pixels (default: 1)
  --no-cdist            disable cumulative distribution of trackpoints
                        (uniform distribution)
  --csv                 also save the heatmap data to a CSV file
```

 :warning: `--zoom` is OpenStreetMap's zoom level, first number after `map=` in [www.openstreetmap.org/#map=](https://www.openstreetmap.org)

Example:  
`strava_local_heatmap.py --gpx-dir ~/GPX --gpx-year 2018 --gpx-filter *Ride*.gpx --zoom 13`

For an explanation on the cumulative distribution function, see:  
https://medium.com/strava-engineering/the-global-heatmap-now-6x-hotter-23fc01d301de

## Output

**heatmap.png**  
![heatmap_zoom.png](output_heatmap.png)

**heatmap.csv**  
See https://umap.openstreetmap.fr/en/map/demo-heatmap_261644 (contribution by [@badele](https://github.com/badele))

## Setup

Run `bash setup.sh && source virtualenv/bin/activate`

### Python dependencies

```
matplotlib==3.0.2
numpy==1.15.4
```

### Other dependencies

Arch Linux (see [here](https://github.com/remisalmon/strava-local-heatmap/pull/3#issuecomment-443541311)): `sudo pacman -S tk`

## Projects using strava_local_heatmap.py

[JeSuisUnDesDeux](https://gitlab.com/JeSuisUnDesDeux/jesuisundesdeux/tree/master/datas/traces)
