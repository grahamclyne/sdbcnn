# https://carpentries-incubator.github.io/geospatial-python/aio/index.html
from pystac_client import Client
import matplotlib.pyplot as plt
from shapely.geometry import Polygon
import geopandas as gpd
import rioxarray
import numpy as np
import xarray as xr
from argparse import ArgumentParser
import os 
import rasterio

#python preprocess.py --file /Users/gclyne/Downloads/1045100064200_201901_RAW_DEM/1045100064200_201901_RAW_DEM.tif
# DATA_PATH = '/home/gclyne/scratch/data'
DATA_PATH = os.environ['SDBCNN_DATA_PATH']
parser = ArgumentParser()
parser.add_argument('--file', type=str)
args = parser.parse_args()
# !gdalinfo /Users/gclyne/Downloads/products/GeoTIFF/NONNA10_4440N06430W.tiff

bathy = rioxarray.open_rasterio(f'{args.file}')

left_lon,lower_lat,right_lon,upper_lat = bathy.rio.transform_bounds('epsg:4326')


file_name = args.file.split('/')[-1].split('_')[0]



bbox={'lonLower':left_lon,'latLower':lower_lat,'lonHigher':right_lon,'latHigher':upper_lat}
# https://carpentries-incubator.github.io/geospatial-python/aio/index.html
# https://data.chs-shc.ca/dashboard/map
# https://stacindex.org/catalogs/earth-search#/Cnz1sryATwWudkxyZekxWx6356v9RmvvCcLLw79uHWJUDvt2?t=2
# catalog = Client.open("https://planetarycomputer.microsoft.com/api/stac/v1")
catalog = Client.open('https://earth-search.aws.element84.com/v0')
# catalog1 = Client.open('https://earthengine-stac.storage.googleapis.com/catalog/COPERNICUS')
mysearch = catalog.search(collections=['sentinel-s2-l2a-cogs'],
                          bbox=[bbox['lonLower'],bbox['latLower'],bbox['lonHigher'],bbox['latHigher']],
                           query =  {"eo:cloud_cover":{"lt":1}},
                          datetime='2019-04-01/2019-10-01', 
                          max_items=10)   

resdict = mysearch.get_all_items()

print(resdict[0])
b02 = rioxarray.open_rasterio(resdict[0].assets['B02'].href)
b03 = rioxarray.open_rasterio(resdict[0].assets['B03'].href)
b04 = rioxarray.open_rasterio(resdict[0].assets['B04'].href)
b08 = rioxarray.open_rasterio(resdict[0].assets['B08'].href)
b11 = rioxarray.open_rasterio(resdict[0].assets['B11'].href)
b12 = rioxarray.open_rasterio(resdict[0].assets['B12'].href)
overview = rioxarray.open_rasterio(resdict[0].assets['overview'].href) #low res image for shape
#use 'visual' asset for true colour image

b11 = b11.rio.reproject_match(b02)
b12 = b12.rio.reproject_match(b02)


poly = Polygon([[left_lon,lower_lat],[right_lon,lower_lat],[right_lon,upper_lat],[left_lon,upper_lat]])

projected_poly = gpd.GeoDataFrame(index=[0], crs='epsg:4326', geometry=[poly])
projected_poly = projected_poly.to_crs(b02.rio.crs)

def process_band(band:xr.DataArray):
    band = band.rio.clip_box(*projected_poly.total_bounds)
    band = band.rio.reproject_match(bathy)
    band = band.where(band != -99999.)
    band = band.rio.interpolate_na() # should i interpolate?
    return band


b02 = process_band(b02)
b03 = process_band(b03)
b04 = process_band(b04)
b08 = process_band(b08)
b11 = process_band(b11)
b12 = process_band(b12)

sat_s2 = np.concatenate((b02,b03,b04,b08,b11,b12),axis=0)



#use if memory problems
# def splitArray(array,var):
#     dim1_step = array.shape[1] // 10 
#     dim2_step = array.shape[2] // 10
#     for i in range(10):
#         subset = array[:,((i) * dim1_step):((i+1) * dim1_step),((i) * dim2_step):((i+1) * dim2_step)]
#         name = var + '_' + file_name + ':' + str(i)
#         np.save(DATA_PATH + '/' + name,subset,allow_pickle=True)

ds_masked = bathy.where(bathy != -99999.) 

# splitArray(sat_s2,'img')
# splitArray(ds_masked,'depth')


np.save(DATA_PATH + 'depth_' + file_name,ds_masked,allow_pickle=True)
np.save(DATA_PATH + 'img_' + file_name,sat_s2,allow_pickle=True)


# Plot
fig, ax = plt.subplots()
fig.set_size_inches((8,8))

# Plot image
overview.plot.imshow(ax=ax)

# Plot crop fields
projected_poly.plot(
    ax=ax,
    edgecolor="red",
)