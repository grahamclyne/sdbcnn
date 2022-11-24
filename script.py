import os

SDBCNN_PROJECT_PATH = os.environ['SDBCNN_PROJECT_PATH']
IMAGE_PATH = '/Users/gclyne/Downloads/products_5/GeoTIFF/'
files = os.listdir('/Users/gclyne/Downloads/products_5/GeoTIFF')



os.system('rm -rf sdbcnn.model')
# os.system('rm data/*')
file_names = []
image_per_depth_image = 1
for i in files:
    file_names.append(i.split('_')[1].split('.')[0])
    os.system(f'python {SDBCNN_PROJECT_PATH}preprocess.py --file {IMAGE_PATH}{i} ')

#reget all images,some will have been filtered out
file_names = list(filter(lambda x: x.startswith('depth_4'),os.listdir('/Users/gclyne/sdbcnn/data/')))
file_names = list(map(lambda x: x.split('_')[1].split('.')[0],file_names))
for i in file_names:
    i = i + '.tiff'
    os.system(f'python {SDBCNN_PROJECT_PATH}collect_all_data.py --img_file img_{i}.npy --depth_file depth_{i}.npy')
for i in file_names:
    i = i + '.tiff'    
    os.system(f'python {SDBCNN_PROJECT_PATH}train_val.py --xtrn rgbnss_trn_{i}.npy --ytrn depth_trn_{i}.npy --log -')
for i in file_names:
    i = i + '.tiff'
    os.system(f'python {SDBCNN_PROJECT_PATH}test.py --xtst rgbnss_tst_{i}.npy --ytst depth_tst_{i}.npy')

files = ','.join(file_names)
os.system(f'python {SDBCNN_PROJECT_PATH}eval.py  --files {files}')



