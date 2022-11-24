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

def clip_band(band):
    return band.rio.clip_box(*projected_poly.total_bounds)

def process_band(band:xr.DataArray):
    band = band.where(band!=band.rio.nodata)
    band = band.fillna(0)
    return band

#python preprocess.py --file /Users/gclyne/Downloads/1045100064200_201901_RAW_DEM/1045100064200_201901_RAW_DEM.tif
# DATA_PATH = '/home/gclyne/scratch/data'
DATA_PATH = os.environ['SDBCNN_DATA_PATH']
parser = ArgumentParser()
parser.add_argument('--file', type=str)
args = parser.parse_args()

bathy = rioxarray.open_rasterio(f'{args.file}')
#transform these coords for s2 image search
left_lon,lower_lat,right_lon,upper_lat = bathy.rio.transform_bounds('epsg:4326')

bbox={'lonLower':left_lon,'latLower':lower_lat,'lonHigher':right_lon,'latHigher':upper_lat}
file_name = args.file.split('/')[-1].split('_')[1]



# https://carpentries-incubator.github.io/geospatial-python/aio/index.html
# https://data.chs-shc.ca/dashboard/map
# https://stacindex.org/catalogs/earth-search#/Cnz1sryATwWudkxyZekxWx6356v9RmvvCcLLw79uHWJUDvt2?t=2
# catalog = Client.open("https://planetarycomputer.microsoft.com/api/stac/v1")
catalog = Client.open('https://earth-search.aws.element84.com/v0')
# catalog1 = Client.open('https://earthengine-stac.storage.googleapis.com/catalog/COPERNICUS')
mysearch = catalog.search(collections=['sentinel-s2-l2a-cogs'],
                          bbox=[bbox['lonLower'],bbox['latLower'],bbox['lonHigher'],bbox['latHigher']],
                           query =  {"eo:cloud_cover":{"lt":1}},
                          datetime='2019-07-01/2019-10-01', 
                          max_items=10)   


resdict = mysearch.get_all_items()
print(file_name)

if(os.path.exists('/Users/gclyne/sdbcnn/data/depth_' + file_name + '.npy')):
    print(file_name, ' already generated')
    exit(0)
def closest(resdict):
    day = 1
    days = []
    for i in resdict:
        print('day of image: ', i , i.datetime.day)
        days.append(i.datetime.day)
    out = list(map(lambda x: x - day,days))
    return np.argmin(out)
for image in resdict:
    print(image)
image = resdict[0]

b01 = rioxarray.open_rasterio(image.assets['B01'].href)
b02 = rioxarray.open_rasterio(image.assets['B02'].href)
b03 = rioxarray.open_rasterio(image.assets['B03'].href)
b04 = rioxarray.open_rasterio(image.assets['B04'].href)
b05 = rioxarray.open_rasterio(image.assets['B05'].href)
b8a = rioxarray.open_rasterio(image.assets['B8A'].href)
b08 = rioxarray.open_rasterio(image.assets['B08'].href)
b09 = rioxarray.open_rasterio(image.assets['B09'].href)
b11 = rioxarray.open_rasterio(image.assets['B11'].href)
b12 = rioxarray.open_rasterio(image.assets['B12'].href)
scl = rioxarray.open_rasterio(image.assets['SCL'].href)
#use 'visual' asset for true colour image
visual = rioxarray.open_rasterio(image.assets['visual'].href) 

b11 = b11.rio.reproject_match(b02)
b12 = b12.rio.reproject_match(b02)
scl = scl.rio.reproject_match(b02)
b01 = b01.rio.reproject_match(b02)
b05 = b05.rio.reproject_match(b02)
b8a = b8a.rio.reproject_match(b02)
b09 = b09.rio.reproject_match(b02)
left_lon,lower_lat,right_lon,upper_lat = bathy.rio.bounds()


poly = Polygon([[left_lon,lower_lat],[right_lon,lower_lat],[right_lon,upper_lat],[left_lon,upper_lat]])
projected_poly_bathy = gpd.GeoDataFrame(index=[0], crs=bathy.rio.crs, geometry=[poly])
projected_poly = projected_poly_bathy.to_crs(b02.rio.crs)
bands = [b02,b03,b04,b08,b11,b12]
# for index in range(10):
#     visual = rioxarray.open_rasterio(resdict[0].assets['visual'].href) #low res image for shape
#     visual = clip_band(visual,pp_scaled)
#     visual.rio.to_raster(f'{resdict[0]}_img.tiff')
bands = list(map(clip_band,bands))
scl = clip_band(scl)
bathy = bathy.rio.clip_box(*projected_poly_bathy.total_bounds)
out = bathy.rio.reproject_match(bands[0])
out = out.where(out!=bathy.rio.nodata)

out = out.where(scl.isel(band=0).values !=10) #thin cirrus
out = out.where(scl.isel(band=0).values !=9) #cloud high probability
out = out.where(scl.isel(band=0).values !=8) #cloud med prob
out = out.where(scl.isel(band=0).values !=2) #cast shadows
out = out.where(scl.isel(band=0).values !=3) #cloud shadows
out = out.fillna(0)


#for visualzing output
out.rio.to_raster(f'clipped_depth_{file_name}.tiff')
clip_band(visual).rio.to_raster(f'clipped_img_{file_name}.tiff')

bands = list(map(process_band,bands))

sat_s2 = np.concatenate(bands,axis=0)

cloud_cover = scl.where((scl == 8) | (scl == 9) | (scl == 10) | (scl == 3) | (scl == 2)).count() / scl.count()
if(cloud_cover < 0.05):
    print('depth shape: ',out.shape)
    print('img shape: ',sat_s2.shape)
    np.save(DATA_PATH +  'depth_' + file_name,out,allow_pickle=True)
    np.save(DATA_PATH + 'img_' + file_name,sat_s2,allow_pickle=True)
    b02.rio.to_raster(file_name + '_s2_img.tiff')



#use if memory problems

# def splitArray(array,var):
#     dim1_step = array.shape[1] // 10 
#     dim2_step = array.shape[2] // 10
#     for i in range(10):
#         subset = array[:,((i) * dim1_step):((i+1) * dim1_step),((i) * dim2_step):((i+1) * dim2_step)]
#         name = var + '_' + file_name + ':' + str(i)
#         np.save(DATA_PATH + '/' + name,subset,allow_pickle=True)

# splitArray(sat_s2,'img')
# splitArray(ds_masked,'depth')
#MASK CLOUDS 


# # Plot
# fig, ax = plt.subplots()
# fig.set_size_inches((8,8))

# # Plot image
# overview.plot.imshow(ax=ax)

# # Plot crop fields
# projected_poly.plot(
#     ax=ax,
#     edgecolor="red",
# )
# fig.save