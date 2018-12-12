# strava_local_heatmap.py

Python script to reproduce the Strava Global Heatmap ([www.strava.com/heatmap](https://www.strava.com/heatmap)) with local GPX data

## Usage:

* Download your GPX files from Strava to the `gpx` folder (see https://support.strava.com/hc/en-us/articles/216918437-Exporting-your-Data-and-Bulk-Export)
* [Optional] Edit the parameters in `strava_local_heatmap.py`:  
`max_nb_tiles` to change the heatmap resolution  
`lat_north_bound,lon_west_bound,lat_south_bound,lon_east_bound` to change the heatmap region (bounding box)
* Run `python3 strava_local_heatmap.py`
* The **heatmap.png** and **heatmap.csv** files are saved to the current directory

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
