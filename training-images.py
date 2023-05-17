"""
Get training data image samples from GOES-16 satellite imagery using IBTrACS
    dataset to identify where the tropical cyclones are.
Author: J. Dylan White
"""

# Import modules
import pandas as pd
import datetime
import numpy as np
from pyproj import Proj
import matplotlib
import matplotlib.pyplot as plt
import time
import warnings
import logging

# Import functions I've written
import goes
import ibtracs

# Don't display plots or warnings
matplotlib.use('Agg')
warnings.filterwarnings('ignore')

# Create and configure logger
logging.basicConfig(format='%(name)s | %(asctime)s | %(levelname)s: %(message)s')
log = logging.getLogger('__name__')
log.setLevel(logging.DEBUG)

# Specify the year to download data for
year = 2017

# Read IBTrACS data and filter by season and just the tropical storms
log.info("Reading validated IBTrACS data")
df = ibtracs.read_data('./data/ibtracs_GOES16.csv',subsetSeason=True,yearStart=year,yearEnd=year)
df = df[df['NATURE']=='TS'].reset_index()

def crop_image(ds,xInd,yInd,buffer,myDPI,figPath):
    
    '''
    From a GOES image, crop an image centered around [yInd,xInd] of size 2*buffer by 2*buffer
    '''

    # Subset the data
    data = ds.Rad[yInd-buffer:yInd+buffer,xInd-buffer:xInd+buffer]

    # Skip if size is 0
    if 0 not in data.shape:

        # Save as netCDF
        data.to_netcdf(figPath.replace("png","nc"))

        # Save as PNG
        f = plt.figure(frameon=False)
        f.set_size_inches(buffer*2/myDPI,buffer*2/myDPI)
        plt.imshow(data,cmap='gray_r');
        plt.axis('off');
        plt.savefig(figPath, facecolor='w', dpi=220, edgecolor='w', bbox_inches='tight', pad_inches=0);
        f.clear();
        plt.close(f);
        del(f)

# Get the starting time
tic = time.perf_counter()

# Set the buffer (in pixels) size
myDPI = 166
buffer = int(myDPI*1.5)

# Loop through all of the dates in the IBTrACS dataframe
for count, date in enumerate(df['ISO_TIME'].unique()):
    
    # Update log file
    log.info(f"Date: {date}")

    # Convert the numpy.datetime64 object into a datetime object
    dt = datetime.datetime.fromisoformat(str(date)[:-3])

    # Update log file
    log.debug("Downloading imagery")
        
    try:

        # Get the image for the specified date
        ds = goes.download_data(date=dt,credPath="secrets.csv",bucketName="noaa-goes16",product='ABI-L1b-RadF',band=13)

        # Update log file
        log.debug("Projecting data")

        # Get dataset projection data
        satHeight = ds.goes_imager_projection.perspective_point_height
        satLon = ds.goes_imager_projection.longitude_of_projection_origin
        satSweep = ds.goes_imager_projection.sweep_angle_axis
        majorMinorAxes = (ds.goes_imager_projection.semi_major_axis,ds.goes_imager_projection.semi_minor_axis)

        # The projection x and y coordinates equals the scanning angle (in radians) multiplied by the satellite height
        x = ds.variables['x'][:] * satHeight
        y = ds.variables['y'][:] * satHeight

        # Create an array of ones for the negative training samples
        nx, ny = ds.Rad.shape
        free = np.ones((ny,nx))

        # Create a pyproj geostationary map object
        p = Proj(proj='geos', h=satHeight, lon_0=satLon, sweep=satSweep)

        # Get the subset of the dataframe that matches this date
        dfSubset = df[df['ISO_TIME'] == date]
        indices = dfSubset.index.values

        # Update log file
        log.debug("Saving cropped images")

        # Loop through all of the subset dataframe rows:
        for i in indices:

            # Get the current row
            row = dfSubset[dfSubset.index==i]

            # Get the latitudes/longitudes of the track data
            trackLat = float(row['LAT'])
            trackLon = float(row['LON'])

            # Convert lon/lat to x/y
            trackX,trackY = p(trackLon,trackLat)

            # Get the closest point to the IBTrACS data
            xInd = np.nanargmin(abs(x-trackX))
            yInd = np.nanargmin(abs(y-trackY))

            # Set the figure file name
            figPart = dt.strftime("%Y%m%d_%HZ")+f'_{xInd:05.0f}_{yInd:05.0f}_{buffer}'
            figPath = f'./data/training/positive/{figPart}_cropped.png'

            # Save the cropped image
            crop_image(ds,xInd,yInd,buffer,myDPI,figPath)

            # Mark these pixels as containing a positive sample
            free[yInd-buffer:yInd+buffer,xInd-buffer:xInd+buffer] = 0

        # Now go find some random negative samples that don't overlap with locations where free == 0
        negativeCount = 0
        maxAttemptCount = 5*len(indices)
        attemptCount = 0
        while negativeCount < len(indices):

            # Get a random location on the image
            xInd = np.random.randint(buffer,nx-buffer,size=1)[0]
            yInd = np.random.randint(buffer,ny-buffer,size=1)[0]

            # Check that it doesn't overlap with previous images
            if (free[yInd-buffer:yInd+buffer,xInd-buffer:xInd+buffer] == 1).all():

                # Set the figure file name
                figPart = dt.strftime("%Y%m%d_%HZ")+f'_{xInd:05.0f}_{yInd:05.0f}_{buffer}'
                figPath = f'./data/training/negative/{figPart}_cropped.png'

                # Save the cropped image
                crop_image(ds,xInd,yInd,buffer,myDPI,figPath)

                # Also mark these pixels, since we have a sample already taken from them
                free[yInd-buffer:yInd+buffer,xInd-buffer:xInd+buffer] = 0

                # Advance the count of negative training sample images obtained
                negativeCount = negativeCount + 1

            # Advance the count of attempts and break if it has been going for too long
            attemptCount = attemptCount + 1
            if attemptCount > maxAttemptCount:
                break

        # Delete the dataset to save memory
        del(ds)

    except:
        log.error("Error saving image")
        
# Get the ending time
toc = time.perf_counter()

# Close the logfile and write out the total time
log.info(f"Total time taken: {toc-tic}")