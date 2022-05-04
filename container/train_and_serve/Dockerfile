# Build an image that can do training and inference in SageMaker
# This is a Python 3 image that uses the nginx, gunicorn, flask stack
# for serving inferences in a stable way.

FROM public.ecr.aws/docker/library/python:3.7-slim

RUN apt-get -y update && apt-get install -y --no-install-recommends \
         wget \
         nginx \
         git \
         ca-certificates

RUN pip install numpy==1.16.2 scipy==1.2.1 catboost pandas flask gevent gunicorn
RUN pip install dvc==2.8.3 s3fs==2021.11.0 dvc[s3]==2.8.3 awscli

# Configure git - change it according to your needs
RUN git config --global user.email "sagemaker-training@example.com"
RUN git config --global user.name "SageMaker TrainingJob User"
RUN git config --global credential.helper '!aws codecommit credential-helper $@'
RUN git config --global credential.UseHttpPath true

# Set some environment variables. PYTHONUNBUFFERED keeps Python from buffering our standard
# output stream, which means that logs can be delivered to the user quickly. PYTHONDONTWRITEBYTECODE
# keeps Python from writing the .pyc files which are unnecessary in this case. We also update
# PATH so that the train and serve programs are found when the container is invoked.

ENV PYTHONUNBUFFERED=TRUE
ENV PYTHONDONTWRITEBYTECODE=TRUE
ENV PATH="/opt/program:${PATH}"

# Set up the program in the image
COPY catboost_regressor /opt/program
WORKDIR /opt/program

