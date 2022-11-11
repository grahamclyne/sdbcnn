#!/bin/bash

#SBATCH --account=def-dmatthew
#SBATCH --time=02:00:00
#SBATCH --mem=50G
#SBATCH --cpus-per-task=32

module load python/3.9 
module load geos
module load proj

source sdbcnn_env/bin/activate
python /home/gclyne/projects/def-dmatthew/gclyne/sdbcnn/preprocess.py --file 1045100064200_201901_RAW_DEM.tif
echo "Preprocess complete"
python /home/gclyne/projects/def-dmatthew/gclyne/sdbcnn/collect_all_data.py
echo "collected data complete"
python /home/gclyne/projects/def-dmatthew/gclyne/sdbcnn/train_val.py
echo "train/validation complete"
python /home/gclyne/projects/def-dmatthew/gclyne/sdbcnn/test.py
echo "test complete"
python /home/gclyne/projects/def-dmatthew/gclyne/sdbcnn/eval.py
echo "validation complete"
python /home/gclyne/projects/def-dmatthew/gclyne/sdbcnn/sdb_gen.py
echo "generation complete"
deactivate
