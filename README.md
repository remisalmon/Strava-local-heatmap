# strava_local_heatmap.py

Python script to reproduce the Strava Global Heatmap (https://www.strava.com/heatmap) with local GPX data

## Usage:

* Download the GPX files from Strava (cf. https://support.strava.com/hc/en-us/articles/216918437-Exporting-your-Data-and-Bulk-Export)
* Copy the GPX files to the `gpx` folder
* Run `python3 strava_local_heatmap.py`
* The heatmap PNG file `heatmap.png` is saved to the current directory

![heatmap.png](heatmap.png)

## Python dependencies:

* Python 3 (tested with Python 3.7.0)
* NumPy
* Matplotlib
* scikit-image (https://scikit-image.org/)

## To Do:

* Calculate `zoom` automatically from the GPX data
