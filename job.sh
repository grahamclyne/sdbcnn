#!/bin/bash

#SBATCH --account=def-dmatthew
#SBATCH --time=02:00:00
#SBATCH --mem=100G
#SBATCH --cpus-per-task=32

module load python/3.9 
module load geos
module load proj
export SDBCNN_PROJECT_PATH=/home/gclyne/projects/def-dmatthew/gclyne/sdbcnn/
export SDBCNN_DATA_PATH=/home/gclyne/scratch/data/

source sdbcnn_env/bin/activate
python ${SDBCNN_PROJECT_PATH}preprocess.py --file /home/gclyne/scratch/1045100064200_201901_RAW_DEM.tif
# python ${SDBCNN_PROJECT_PATH}preprocess.py --file /home/gclyne/scratch/1045150064200_201901_RAW_DEM.tif
# python ${SDBCNN_PROJECT_PATH}preprocess.py --file /home/gclyne/scratch/1045200064100_201901_RAW_DEM.tif
# python ${SDBCNN_PROJECT_PATH}preprocess.py --file /home/gclyne/scratch/1045250064000_201901_RAW_DEM.tif
echo "Preprocess complete"
python ${SDBCNN_PROJECT_PATH}collect_all_data.py --img_file img_1045100064200.npy --depth_file depth_1045100064200.npy
# python ${SDBCNN_PROJECT_PATH}collect_all_data.py --img_file img_1045150064200.npy --depth_file depth_1045150064200.npy
# python ${SDBCNN_PROJECT_PATH}collect_all_data.py --img_file img_1045200064100.npy --depth_file depth_1045200064100.npy
# python ${SDBCNN_PROJECT_PATH}collect_all_data.py --img_file img_1045250064000.npy --depth_file depth_1045250064000.npy
echo "collected data complete"
python ${SDBCNN_PROJECT_PATH}train_val.py --xtrn rgbnss_trn_1045100064200.npy --ytrn depth_trn_1045100064200.npy --log - 
# python ${SDBCNN_PROJECT_PATH}train_val.py --xtrn rgbnss_trn_1045150064200.npy --ytrn depth_trn_1045150064200.npy --log - 
# python ${SDBCNN_PROJECT_PATH}train_val.py --xtrn rgbnss_trn_1045200064100.npy --ytrn depth_trn_1045200064100.npy --log - 
# python ${SDBCNN_PROJECT_PATH}train_val.py --xtrn rgbnss_trn_1045250064000.npy --ytrn depth_trn_1045250064000.npy --log - 
echo "train/validation complete"
python ${SDBCNN_PROJECT_PATH}test.py --xtst rgbnss_tst_1045100064200.npy --ytst depth_tst_1045100064200.npy
# python ${SDBCNN_PROJECT_PATH}test.py --xtst rgbnss_tst_1045150064200.npy --ytst depth_tst_1045150064200.npy
# python ${SDBCNN_PROJECT_PATH}test.py --xtst rgbnss_tst_1045200064100.npy --ytst depth_tst_1045200064100.npy
# python ${SDBCNN_PROJECT_PATH}test.py --xtst rgbnss_tst_1045250064000.npy --ytst depth_tst_1045250064000.npy
echo "test complete"
python ${SDBCNN_PROJECT_PATH}eval.py --pred depth_pred_1045100064200.npy --tst depth_tst_1045100064200.npy
# python ${SDBCNN_PROJECT_PATH}eval.py --pred depth_pred_1045150064200.npy --tst depth_tst_1045150064200.npy
# python ${SDBCNN_PROJECT_PATH}eval.py --pred depth_pred_1045200064200.npy --tst depth_tst_1045200064200.npy
# python ${SDBCNN_PROJECT_PATH}eval.py --pred depth_pred_1045250064200.npy --tst depth_tst_1045250064200.npy
echo "validation complete"
#python /home/gclyne/projects/def-dmatthew/gclyne/sdbcnn/sdb_gen.py
# echo "generation complete"
deactivate
