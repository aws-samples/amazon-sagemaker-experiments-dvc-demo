# SageMaker Experiments and DVC

This sample shows how to use DVC within the SageMaker environment.
In particular, we will look at how to build a custom image with DVC libraries installed by default to provide a consistent environment to your data scientists.
FUrthermore, we show how you can integrate SageMaker Trainings and SageMaker Experiments with a DVC workflow.

## Prerequisite

* An AWS Account
* An IAM user with Admin permissions

## Setup

We suggest for the initial setup, to use Cloud9 on a `t3.large` instance type.

### Build a custom SageMaker Studio image with DVC already installed

See instructions [here](./sagemaker-studio-dvc-image/README.md)

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the [LICENSE](LICENSE) file.

