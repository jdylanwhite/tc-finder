import datetime
import xarray as xr
import requests
import netCDF4
import boto3

def day_of_year(date):

    """
    Take a datetime date and get the number of days since Jan 1 of that same year

    Args:
        date (datetime.datetime): the date to find the day of year
    """
    
    year = date.year
    firstDay = datetime.datetime(year,1,1)
    return (date-firstDay).days+1

def read_aws_creds(credPath):
    '''
    Read AWS credentials stored in a CSV file

    Args:
        credPath (str): the path to the credentials CSV
    '''

    with open(credPath,'r') as f:
        creds = f.read()

    return creds.split('\n')[1].split(',')

def get_s3_keys(bucket, s3Client, prefix = ''):

    """
    Generate the keys in an S3 bucket.
    
    Args:
        bucket (str): the name of the S3 bucket
        s3Client (str): the AWS SDK client
    """
    
    # Build arguments dictionary
    kwargs = {'Bucket': bucket}
    if isinstance(prefix, str):
        kwargs['Prefix'] = prefix

    while True:

        resp = s3Client.list_objects_v2(**kwargs)
        for obj in resp['Contents']:
            key = obj['Key']
            if key.startswith(prefix):
                yield key

        try:
            kwargs['ContinuationToken'] = resp['NextContinuationToken']
        except KeyError:
            break

def download_data(date,credPath,bucketName,product='ABI-L1b-RadF',band=3):

    """
    Retrieve GOES full-disc image from AWS storage
    
    Args:
        date (datetime.datetime): the date/time for the image
        credPath (str): the path to the credentials CSV
        bucketName (str): the AWS bucket for the image
        product (str): the product name in the file to download
        band (int): the image band to download
    """

    # Set date of image
    year = date.year
    day = day_of_year(date)
    hour = date.hour

    # Identify scan mode based on date
    if date < datetime.datetime(2019,4,2,16):
        scanMode = "M3"
    else:
        scanMode = "M6"

    # Initialize S3 client with credentials
    keyID,key = read_aws_creds(credPath)
    s3Client = boto3.client('s3',aws_access_key_id=keyID,aws_secret_access_key=key)

    # Set the file prefix string
    prefix = f'{product}/{year}/{day:03.0f}/{hour:02.0f}/OR_{product}-{scanMode}C{band:02.0f}'

    # Get the keys from the S3 bucket
    keys = get_s3_keys(bucketName,s3Client,prefix)

    # Selecting the first measurement taken within the hour
    key = [key for key in keys][0] 

    # Send a request to the bucket
    resp = requests.get(f'https://{bucketName}.s3.amazonaws.com/{key}')

    # Open the GOES 16 image
    fileName = key.split('/')[-1].split('.')[0]
    nc4 = netCDF4.Dataset(fileName,memory=resp.content)
    store = xr.backends.NetCDF4DataStore(nc4)
    ds = xr.open_dataset(store)

    return ds