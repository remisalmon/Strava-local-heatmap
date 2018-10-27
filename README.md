# strava_heatmap.py

## Usage:

* Download the GPX files from Strava to the `./gpx/` folder (cf. https://support.strava.com/hc/en-us/articles/216918437-Exporting-your-Data-and-Bulk-Export)
* Run ` python ./strava_heatmap.py`, the heatmap PNG file `heatmap.png` is saved in the current directory

![heatmap.png](heatmap.png)

## Python dependencies:

* NumPy
* Matplotlib
* scikit-image (https://scikit-image.org/)

## ToDo:

* Extract trackpoints elevation
* Calculate trackpoints speed + modulate with elevation gradient
