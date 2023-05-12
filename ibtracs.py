import os
import pandas as pd
from urllib import request

def download_data(basin="NA",dataDir="./data/",overwrite=True) -> str:

    """
    Download IBTrACS data from desired basin

    Args:
        basin (str): The basin shortname used in IBTrACS datasets
        datadir (str): The directory to download the data
        overwrite (bool): Option to overwrite the file if it already exists
    """

    # Set the URL
    url = 'https://www.ncei.noaa.gov/data/'+\
          'international-best-track-archive-for-climate-stewardship-ibtracs/'+\
          'v04r00/access/csv/ibtracs.'+basin+'.list.v04r00.csv'

    # Set the file path
    filePath = dataDir+'ibtracs_'+basin+'.csv'

    # Download the file if it doesn't already exists
    if overwrite or not os.path.exists(filePath):
            request.urlretrieve(url,filePath)

    return filePath

def read_data(filePath,subsetSeason=False,yearStart=2010,yearEnd=2020):

    """
    Read IBTrACS data to a pandas data frame, subset seasons if needed

    Args:
        filePath (str): the path of the IBTrACS file to read
        subsetSeason (bool): option to subset the data based on season
        yearStart (int): the season to start the subset
        yearEnd (int): the season to end the subset
    """

    # Read the data from the CSV
    df = pd.read_csv(filePath,low_memory=False,skiprows=range(1,2))

    # Only keep a handful of columns
    keepColumns = ['SID','SEASON','NUMBER','NAME','ISO_TIME',
                'NATURE','LAT','LON','WMO_WIND','WMO_PRES','TRACK_TYPE',
                'DIST2LAND','LANDFALL','IFLAG','STORM_SPEED','STORM_DIR']
    df = df[keepColumns]

    # Convert time strings to datetimes for better querying
    df['ISO_TIME'] = pd.to_datetime(df['ISO_TIME'])
    df['SEASON'] = pd.to_numeric(df['SEASON'])
    df['NUMBER'] = pd.to_numeric(df['NUMBER'])
    df['LAT'] = pd.to_numeric(df['LAT'])
    df['LON'] = pd.to_numeric(df['LON'])

    # Subset seasons
    if subsetSeason:
        df = df[(df['SEASON'] >= yearStart) & (df['SEASON'] <= yearEnd)]

    return df