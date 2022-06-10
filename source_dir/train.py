import glob
import logging
import os
import json
import re
import subprocess
import traceback
import sys

import argparse
import joblib

from sklearn.ensemble import RandomForestRegressor
from catboost import CatBoostRegressor

import numpy as np
import pandas as pd

prefix = '/opt/ml/'
input_path = prefix + 'input/data'
dataset_path = prefix + 'input/data/dataset'
train_channel_name = 'train'
validation_channel_name = 'validation'

output_path = os.path.join(prefix, 'output')
model_path = os.path.join(prefix, 'model')
model_file_name = 'catboost-regressor-model.dump'
#model_file_name = 'model.joblib'
train_path = os.path.join(dataset_path, train_channel_name)
validation_path = os.path.join(dataset_path, validation_channel_name)

def fetch_data_from_dvc(dvc_repo_url, dvc_branch):
    print(f"Configure git to pull authenticated from CodeCommit")
    print(f"Cloning repo: {dvc_repo_url}, git branch: {dvc_branch}")
    subprocess.check_call(["git", "clone", "--depth", "1", "--branch", dvc_branch, dvc_repo_url, input_path])
    print("dvc pull")
    os.chdir(input_path + "/dataset/")
    subprocess.check_call(["dvc", "pull"])

# Model serving
"""
Deserialize fitted model
"""
def model_fn(model_dir):
    model = CatBoostRegressor()
    model.load_model(os.path.join(model_path, model_file_name))
    return model

if __name__ == '__main__':
    print("extracting arguments")
    parser = argparse.ArgumentParser()

    # hyperparameters sent by the client are passed as command-line arguments to the script.
    # to simplify the demo we don't use all sklearn RandomForest hyperparameters
    parser.add_argument("--learning_rate", type=int, default=1)
    parser.add_argument("--depth", type=int, default=5)
    
    args, _ = parser.parse_known_args()
    
    dvc_repo_url = os.environ.get('DVC_REPO_URL')
    dvc_branch = os.environ.get('DVC_BRANCH')

    fetch_data_from_dvc(dvc_repo_url, dvc_branch)
    
    print('Starting the training.')

    try:
        # Take the set of train files and read them all into a single pandas dataframe
        train_input_files = [os.path.join(train_path, file) for file in glob.glob(train_path+"/*.csv")]
        if len(train_input_files) == 0:
            raise ValueError(('There are no files in {}.\n' +
                              'This usually indicates that the channel ({}) was incorrectly specified,\n' +
                              'the data specification in S3 was incorrectly specified or the role specified\n' +
                              'does not have permission to access the data.').format(train_path, train_channel_name))
        print('Found train files: {}'.format(train_input_files))
        train_df = pd.DataFrame()
        for file in train_input_files:
            if train_df.shape[0] == 0:
                train_df = pd.read_csv(file)
            else:
                df = pd.read_csv(file)
                train_df.append(df, ignore_index=True)

        # Take the set of train files and read them all into a single pandas dataframe
        validation_input_files = [os.path.join(validation_path, file) for file in glob.glob(validation_path+"/*.csv")]
        if len(validation_input_files) == 0:
            raise ValueError(('There are no files in {}.\n' +
                              'This usually indicates that the channel ({}) was incorrectly specified,\n' +
                              'the data specification in S3 was incorrectly specified or the role specified\n' +
                              'does not have permission to access the data.').format(validation_path, train_channel_name))
        print('Found validation files: {}'.format(validation_input_files))
        validation_df = pd.DataFrame()
        for file in validation_input_files:
            if validation_df.shape[0] == 0:
                validation_df = pd.read_csv(file)
            else:
                df = pd.read_csv(file)
                validation_df.append(df, ignore_index=True)

        # Assumption is that the label is the last column
        print('building training and validation datasets')
        X_train = train_df.iloc[:, 1:].values
        y_train = train_df.iloc[:, 0:1].values
        X_validation = validation_df.iloc[:, 1:].values
        y_validation = validation_df.iloc[:, 0:1].values

        # define and train model
        model = CatBoostRegressor(learning_rate=args.learning_rate, depth=args.depth)

        model.fit(X_train, y_train, eval_set=(X_validation, y_validation), logging_level='Silent')

        # print abs error
        print('validating model')
        abs_err = np.abs(model.predict(X_validation) - y_validation)

        # print couple perf metrics
        for q in [10, 50, 90]:
            print('AE-at-' + str(q) + 'th-percentile: '+ str(np.percentile(a=abs_err, q=q)))

        # persist model
        # path = os.path.join(model_path, model_file_name)
        # joblib.dump(model, path)
        path = os.path.join(model_path, model_file_name)
        model.save_model(path)

        print('Training complete.')
        
    except Exception as e:
        # Write out an error file. This will be returned as the failureReason in the
        # DescribeTrainingJob result.
        trc = traceback.format_exc()
        with open(os.path.join(output_path, 'failure'), 'w') as s:
            s.write('Exception during training: ' + str(e) + '\n' + trc)
        # Printing this causes the exception to be in the training job logs, as well.
        print('Exception during training: ' + str(e) + '\n' + trc)
        # A non-zero exit dependencies causes the training job to be marked as Failed.
        sys.exit(255)

    # A zero exit dependencies causes the job to be marked a Succeeded.
    sys.exit(0)
