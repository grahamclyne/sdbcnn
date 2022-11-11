# https://carpentries-incubator.github.io/geospatial-python/aio/index.html
from pystac_client import Client
import matplotlib.pyplot as plt
from shapely.geometry import Polygon
import geopandas as gpd
import rioxarray
import numpy as np
import xarray as xr
from argparse import ArgumentParser


parser = ArgumentParser()
parser.add_argument('--file', type=str)
args = parser.parse_args()
# !gdalinfo /Users/gclyne/Downloads/products/GeoTIFF/NONNA10_4440N06430W.tiff
# https://gis.stackexchange.com/questions/57834/how-to-get-raster-corner-coordinates-using-python-gdal-bindings

from osgeo import gdal 
src = gdal.Open(f'/home/gclyne/scratch/{args.file}')
ulx, xres, xskew, uly, yskew, yres  = src.GetGeoTransform()
lrx = ulx + (src.RasterXSize * xres)
lry = uly + (src.RasterYSize * yres)

from osgeo import osr

# Setup the source projection - you can also import from epsg, proj4...
source = osr.SpatialReference()
source.ImportFromWkt(src.GetProjection())

# The target projection
target = osr.SpatialReference()
target.ImportFromEPSG(4326)

# Create the transform - this can be used repeatedly
transform = osr.CoordinateTransformation(source, target)

# Transform the point. You can also create an ogr geometry and use the more generic `point.Transform()`
ulat,llon,_ = transform.TransformPoint(ulx, uly)
llat,rlon,_ = transform.TransformPoint(lrx,lry)








bbox={'lonLower':llon,'latLower':llat,'lonHigher':rlon,'latHigher':ulat}
# https://carpentries-incubator.github.io/geospatial-python/aio/index.html
# https://data.chs-shc.ca/dashboard/map
# https://stacindex.org/catalogs/earth-search#/Cnz1sryATwWudkxyZekxWx6356v9RmvvCcLLw79uHWJUDvt2?t=2
# catalog = Client.open("https://planetarycomputer.microsoft.com/api/stac/v1")
catalog = Client.open('https://earth-search.aws.element84.com/v0')
# catalog1 = Client.open('https://earthengine-stac.storage.googleapis.com/catalog/COPERNICUS')
mysearch = catalog.search(collections=['sentinel-s2-l2a-cogs'],
                          bbox=[bbox['lonLower'],bbox['latLower'],bbox['lonHigher'],bbox['latHigher']],
                        #   query =  {"eo:cloud_cover":{"lt":1}},
                          datetime='2019-01-01/2019-02-01', 
                          max_items=10)   

resdict = mysearch.get_all_items()

print('using ' + resdict[0])
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


poly = Polygon([[llon,llat],[rlon,llat],[rlon,ulat],[llon,ulat]])

projected_poly = gpd.GeoDataFrame(index=[0], crs='epsg:4326', geometry=[poly])
projected_poly = projected_poly.to_crs(b02.rio.crs)

bathy = rioxarray.open_rasterio(f'/home/gclyne/scratch/{args.file}')
def process_band(band:xr.DataArray):
    band = band.rio.clip_box(*projected_poly.total_bounds)
    band = band.rio.reproject_match(bathy)
    band = band.rio.interpolate_na()
    return band


b02 = process_band(b02)
b03 = process_band(b03)
b04 = process_band(b04)
b08 = process_band(b08)
b11 = process_band(b11)
b12 = process_band(b12)

sat_s2 = np.concatenate((b02,b03,b04,b08,b11,b12),axis=0)


np.save('img',sat_s2,allow_pickle=True)


#use if memory problems
# def splitArray(array,bound,var):
#     text_file = open("./data/f" + var + "_list.txt", "w")
#     dim1_step = array.shape[1] // 10 
#     dim2_step = array.shape[2] // 10
#     for i in range(10):
#         subset = array[:,((i) * dim1_step):((i+1) * dim1_step),((i) * dim2_step):((i+1) * dim2_step)]
#         name = var + '_' + resdict[0].id.split('_')[2] + '_' + str(i)
#         np.save('./data/' + name,subset,allow_pickle=True)
#         text_file.write('./data/' + name + '.npy\n')
#     text_file.close()

# splitArray(sat_s2,max(sat_s2.shape),'img')
# splitArray(bathy,max(bathy.shape),'depth')


ds_masked = bathy.where(bathy != -99999.) 
np.save('depth',ds_masked.values[:,0:1000,0:1000],allow_pickle=True)


# Plot
# fig, ax = plt.subplots()
# fig.set_size_inches((8,8))

# # Plot image
# overview.plot.imshow(ax=ax)

# # Plot crop fields
# projected_poly.plot(
#     ax=ax,
#     edgecolor="red",
# )