## Conda Environments as Kernels

This tutorial explains how to create a custom image for Amazon SageMaker Studio that has DVC already installed.
The advantage of creating an image and make it available to all SageMaker Studio users is that it creates a consistent environment for the SageMake Studio users, which they could also run locally.

This tutorial is heavily inspired by [this example](https://github.com/aws-samples/sagemaker-studio-custom-image-samples/tree/main/examples/conda-env-kernel-image).
Further information about custom images for SageMaker Studio can be found [here](https://docs.aws.amazon.com/sagemaker/latest/dg/studio-byoi.html)

### Prerequisite

* An AWS account
* an IAM user with enough permissions (`AmazonEC2ContainerRegistryFullAccess`, and `SageMakerFullAccess`)
* a SageMaker Domain already created

### Overview

This custom image sample demonstrates how to create a custom Conda environment in a Docker image and use it as a custom kernel in SageMaker Studio.

The Conda environment must have the appropriate kernel package installed, for e.g., `ipykernel` for a Python kernel. This example creates a Conda environment called `myenv` with a few Python packages (see [environment.yml](environment.yml)) and the `ipykernel`. SageMaker Studio will automatically recognize this Conda environment as a kernel named `conda-env-myenv-py` (See  [app-image-config-input.json](app-image-config-input.json))

### Building the image

## Resize Cloud9

```bash
cd ~/sagemaker-dvc-catboost-demo/sagemaker-studio-dvc-image
./resize-cloud9.sh 20
```
Set the enviromental variables

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
# Build and push the image
aws --region ${REGION} ecr get-login-password | docker login --username AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/smstudio-custom

docker build . -t ${IMAGE_NAME} -t ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/smstudio-custom:${IMAGE_NAME}
docker push ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/smstudio-custom:${IMAGE_NAME}
```

### Using with SageMaker Studio

Create a SageMaker Image (SMI) with the image in ECR. 

```bash
# Role in your account to be used for SMI. Modify as required.
export ROLE_ARN=arn:aws:iam::${ACCOUNT_ID}:role/RoleName
```

```bash
aws --region ${REGION} sagemaker create-image \
    --image-name ${IMAGE_NAME} \
    --role-arn ${ROLE_ARN}

aws --region ${REGION} sagemaker create-image-version \
    --image-name ${IMAGE_NAME} \
    --base-image "${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/smstudio-custom:${IMAGE_NAME}"

# Verify the image-version is created successfully. Do NOT proceed if image-version is in CREATE_FAILED state or in any other state apart from CREATED.
aws --region ${REGION} sagemaker describe-image-version --image-name ${IMAGE_NAME}
```

Create a AppImageConfig for this image

```bash
aws --region ${REGION} sagemaker create-app-image-config --cli-input-json file://app-image-config-input.json
```

Create a Domain, providing the SageMaker Image and AppImageConfig in the Domain input. Replace the placeholders for VPC ID, Subnet IDs, and Execution Role in `create-domain-input.json`

Find the default vpc id, and its public subnets
```bash
aws ec2 describe-vpcs --filters Name=is-default,Values=true | jq -r '.Vpcs[].VpcId'
```
```bash
aws ec2 describe-subnets --filters Name=vpc-id,Values=$(aws ec2 describe-vpcs --filters Name=is-default,Values=true | jq -r '.Vpcs[].VpcId') | jq -r '.Subnets[].SubnetId'
```

```bash
aws --region ${REGION} sagemaker create-domain --cli-input-json file://create-domain-input.json
```

If you have an existing Domain, you can also use the `update-domain`

```bash
aws --region ${REGION} sagemaker update-domain --cli-input-json file://update-domain-input.json
```

Create a User Profile, and start a Notebook using the SageMaker Studio launcher.