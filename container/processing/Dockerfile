FROM public.ecr.aws/docker/library/python:3.7-slim

RUN apt-get -y update && apt-get install -y --no-install-recommends wget git

RUN pip3 install numpy pandas scikit-learn==1.0.2
RUN pip3 install sagemaker-experiments==0.1.35
RUN pip3 install git-remote-codecommit
RUN pip3 install dvc==2.8.3 s3fs==2021.11.0 dvc[s3]==2.8.3

# Configure git

RUN git config --global user.email "sagemaker-processing@example.com"
RUN git config --global user.name "SageMaker ProcessingJob User"

ENV PYTHONUNBUFFERED=TRUE

ENTRYPOINT ["python3"]
