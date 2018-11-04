# strava_heatmap.py

## Usage:

* Download the GPX files from Strava (cf. https://support.strava.com/hc/en-us/articles/216918437-Exporting-your-Data-and-Bulk-Export)
* Copy the GPX files to the `./gpx/` folder
* Run `python3 ./strava_heatmap.py`
* The heatmap PNG file `heatmap.png` is saved to the current directory

![heatmap.png](heatmap.png)

## Python dependencies:

* NumPy
* Matplotlib
* scikit-image (https://scikit-image.org/)

## To Do:

* Calculate `zoom` automatically from lat, lon data
