# SageMaker Experiments and DVC

This sample shows how to use DVC within the SageMaker environment.
In particular, we will look at how to build a custom image with DVC libraries installed by default to provide a consistent environment to your data scientists.
FUrthermore, we show how you can integrate SageMaker Processing, SageMaker Trainings and SageMaker Experiments with a DVC workflow.

## Prerequisite

* An AWS Account
* An IAM user with Admin permissions

## Setup

We suggest for the initial setup, to use Cloud9 on a `t3.large` instance type.

### Build a custom SageMaker Studio image with DVC already installed

See instructions [here](./sagemaker-studio-dvc-image/README.md)

### Execute the sample notebook

We provide two sample notebooks to see how to use DVC in combination with SageMaker:

* one that installs DVC in script mode by passing a `requirements.txt` file to both the processing job and the training job [dvc_sagemaker_script_mode.ipynb](./dvc_sagemaker_script_mode.ipynb);
* one that shows how to create the container for the processing jobs, the training jobs, and the inference [dvc_sagemaker_byoc.ipynb](./dvc_sagemaker_byoc.ipynb).

Both notebooks are meant to be used within SageMaker Studio with the custom image created before.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the [LICENSE](LICENSE) file.