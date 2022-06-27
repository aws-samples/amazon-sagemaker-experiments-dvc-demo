# SageMaker Experiments and DVC

This sample shows how to use DVC within the SageMaker environment.
In particular, we will look at how to build a custom image with DVC libraries installed by default to provide a consistent environment to your data scientists.
FUrthermore, we show how you can integrate SageMaker Processing, SageMaker Trainings and SageMaker Experiments with a DVC workflow.

## Prerequisite

* An AWS Account
* An IAM user with Admin-like permissions

If you do not have Admin-like permissions, we reccomend to have at least the following permissions:
* Administer Amazon ECR
* Administer a SageMaker Studio Domain
* Administer S3 (or at least any buckets with *sagemaker* in the bucket name)
* Create IAM Roles
* Create a Cloud9 environment

## Setup

We suggest for the initial setup, to use Cloud9 on a `t3.large` instance type.

## Build a custom SageMaker Studio image with DVC already installed

We aim to explains how to create a custom image for Amazon SageMaker Studio that has DVC already installed.
The advantage of creating an image and make it available to all SageMaker Studio users is that it creates a consistent environment for the SageMake Studio users, which they could also run locally.

This tutorial is heavily inspired by [this example](https://github.com/aws-samples/sagemaker-studio-custom-image-samples/tree/main/examples/conda-env-kernel-image).
Further information about custom images for SageMaker Studio can be found [here](https://docs.aws.amazon.com/sagemaker/latest/dg/studio-byoi.html)

### Overview

This custom image sample demonstrates how to create a custom Conda environment in a Docker image and use it as a custom kernel in SageMaker Studio.

The Conda environment must have the appropriate kernel package installed, for e.g., `ipykernel` for a Python kernel.
This example creates a Conda environment called `dvc` with a few Python packages (see [environment.yml](environment.yml)) and the `ipykernel`.
SageMaker Studio will automatically recognize this Conda environment as a kernel named `conda-env-dvc-py`.

#### Clone the GitHub repository 
```bash
git clone https://github.com/aws-samples/amazon-sagemaker-experiments-dvc-demo
```

#### Resize Cloud9

```bash
cd ~/environment/amazon-sagemaker-experiments-dvc-demo/sagemaker-studio-dvc-image/
./resize-cloud9.sh 20
```

### Build the Docker images for SageMaker Studio

Set some basic environment variables

```bash
sudo yum install jq -y
export REGION=$(curl -s 169.254.169.254/latest/dynamic/instance-identity/document | jq -r '.region')
echo "export REGION=${REGION}" | tee -a ~/.bash_profile

export ACCOUNT_ID=$(aws sts get-caller-identity | jq -r '.Account')
echo "export ACCOUNT_ID=${ACCOUNT_ID}" | tee -a ~/.bash_profile

export IMAGE_NAME=conda-env-dvc-kernel
echo "export IMAGE_NAME=${IMAGE_NAME}" | tee -a ~/.bash_profile
```

Build the Docker image and push to Amazon ECR.

```bash
# Login to ECR
aws --region ${REGION} ecr get-login-password | docker login --username AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/smstudio-custom

# Create the ECR repository
aws --region ${REGION} ecr create-repository --repository-name smstudio-custom

# Build the image - it might take a few minutes to complete this step
docker build . -t ${IMAGE_NAME} -t ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/smstudio-custom:${IMAGE_NAME}
# Push the image to ECR
docker push ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/smstudio-custom:${IMAGE_NAME}
```

### Associate a custom image to SageMaker Studio

#### Prepare the environment to deploy with CDK

Step 1: Navigate to the `cdk` directory:

```bash
cd ~/environment/amazon-sagemaker-experiments-dvc-demo/sagemaker-studio-dvc-image/cdk
```

Step 2: Create a virtual environment:

```bash
python3 -m venv .cdk-venv
```

Step 3: Activate the virtual environment after the init process completes, and the virtual environment is created:

```bash
source .cdk-venv/bin/activate
```

Step 4: Install the required dependencies:

```bash
pip3 install --upgrade pip
pip3 install -r requirements.txt
```

Step 5: Install and bootstrap CDK v2 (The latest CDK version tested was `2.27.0`)

```bash
npm install -g aws-cdk@2.27.0 --force
cdk bootstrap
```

#### Create a new SageMaker Studio
( Skip to [Update an existing SageMaker Studio](#update-an-existing-sagemaker-studio) if you have already an existing SageMaker Studio domain)

Step 5: deploy CDK (CDK will deploy a stack named: `sagemakerStudioCDK` which you can verify in `CloudFormation`)

```bash
cdk deploy --require-approval never
```

CDK will create the following resources via` CloudFormation`:
* provisions a new SageMaker Studio domain
* creates and attaches a SageMaker execution role, i.e., `RoleForSagemakerStudioUsers` with the right permissions to the SageMaker Studio domain
* creates a SageMaker Image and a SageMaker Image Version from the docker image `conda-env-dvc-kernel` we have created earlier
* creates an AppImageConfig which specify how the kernel gateway should be configured
* provision a SageMaker Studio user, i.e., `data-scientist-dvc`, with the correct SageMaker execution role and makes available the custom SageMaker Studio image available to it

#### Update an existing SageMaker Studio

If you have an existing SageMaker Studio environment, we need to first retrieve the exising SageMaker Studio domain ID, deploy a "reduced" version of the CDK stack, and update the SageMaker Studio domain configuration.

Step 5: Set the `DOMAIN_ID` environment variable with your domain ID and save to your `bash_profile`.

```bash
export DOMAIN_ID=$(aws sagemaker list-domains | jq -r '.Domains[0].DomainId')
echo "export DOMAIN_ID=${DOMAIN_ID}" | tee -a ~/.bash_profile
```

Step 6: deploy CDK (by setting the `DOMAIN_ID` environment variable, CDK will deploy a stack named: `sagemakerUserCDK` which you can verify on `CloudFormation`)

```bash
cdk deploy --require-approval never
```

CDK will create the following resources via` CloudFormation`:
* creates and attaches a SageMaker execution role, i.e., `RoleForSagemakerStudioUsers` with the right permissions to your existing SageMaker Studio domain
* creates a SageMaker Image and a SageMaker Image Version from the docker image `conda-env-dvc-kernel` we have created earlier
* creates an AppImageConfig which specify how the kernel gateway should be configured
* provision a SageMaker Studio user, i.e., `data-scientist-dvc`, with the correct SageMaker execution role and makes available the custom SageMaker Studio image available to it

Step 7: Update the SageMaker Studio domain configuration

```bash
# inject your DOMAIN_ID into the configuration file
sed -i 's/<your-sagemaker-studio-domain-id>/'"$DOMAIN_ID"'/' ../update-domain-input.json

# update the sagemaker studio domain
aws --region ${REGION} sagemaker update-domain --cli-input-json file://../update-domain-input.json
```

Open the newly created SageMaker Studio user, i.e., `data-scientist-dvc`.

![image info](./img/studio-custom-image-select.png)


### Execute the sample notebook

In the SageMaker Studio domain, launch `Studio` for the `data-scientist-dvc`.
Open a terminal and clone the repository

```bash
git clone https://github.com/aws-samples/amazon-sagemaker-experiments-dvc-demo
```

and open the [dvc_sagemaker_script_mode.ipynb](./dvc_sagemaker_script_mode.ipynb) notebook.

When prompted, ensure that you select the Custom Image `conda-env-dvc-kernel` as shown below

We provide two sample notebooks to see how to use DVC in combination with SageMaker:

* one that installs DVC in script mode by passing a `requirements.txt` file to both the processing job and the training job [dvc_sagemaker_script_mode.ipynb](./dvc_sagemaker_script_mode.ipynb);
* one that shows how to create the container for the processing jobs, the training jobs, and the inference [dvc_sagemaker_byoc.ipynb](./dvc_sagemaker_byoc.ipynb).

Both notebooks are meant to be used within SageMaker Studio with the custom image created before.

## Cleanup

Before removing all resources created, you need to make sure that all Apps are deleted from the `data-scientist-dvc` user, i.e. all `KernelGateway` apps, as well as the default `JupiterServer`.

Once done, you can destroy the CDK stack by running

```bash
cd ~/environment/amazon-sagemaker-experiments-dvc-demo/sagemaker-studio-dvc-image/cdk
cdk destroy
```

In case you started off from an existing domain, please also execute the following command:

```bash
# inject your DOMAIN_ID into the configuration file
sed -i 's/<your-sagemaker-studio-domain-id>/'"$DOMAIN_ID"'/' ../update-domain-no-custom-images.json

# update the sagemaker studio domain
aws --region ${REGION} sagemaker update-domain --cli-input-json file://../update-domain-no-custom-images.json
```

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the [LICENSE](LICENSE) file.