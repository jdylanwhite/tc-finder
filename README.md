# Tropical Cyclone Finder

In this project, I want to explore how I can apply machine learning to tropical cyclones (TC). Some ideas I have for now are:

* Given a synoptic scale cropped satellite image, classify the image as containing TC or not
* Given a synoptic scale cropped satellite image, detect where on the image the TC is located if it exists
* Given a planetary scale satellite image, detect where on the image the TC is located if it exists
* Given several layers (satellite images, meteorological quantities), assess the probability of a TC forming

## Exploratory Data Anaylsis

The `eda` directory is a space for exploring data. The notebooks in this directory explore:

* IBTrACS - Load and explore IBTrACS data, a source of tropical cyclone tracking.
* GOES - Load and explore GOES satellite imagery data stored on Amazon Web Services.
* GOES and IBTrACS - Load both IBTrACS and GOES data, project both data into the same geographic projection, and overlay the track data of a hurricane on a image.