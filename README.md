# strava_heatmap

## Usage:

* Download the GPX files from Strava to the `./gpx/` folder (cf. https://support.strava.com/hc/en-us/articles/216918437-Exporting-your-Data-and-Bulk-Export)
* Run `python ./strava_heatmap.py`, the heatmap PNG file (heatmap.png) are saved in the current directory

![heatmap.png](heatmap.png)

## ToDo:

* FIX: Gaussian kernel sigma should be proportional to trackpoints density (cf. https://en.wikipedia.org/wiki/Sum_of_normally_distributed_random_variables#Independent_random_variables)
* Calculate trackpoints speed + modulation with elevation gradient
