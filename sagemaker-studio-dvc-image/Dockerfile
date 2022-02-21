FROM continuumio/miniconda3:4.10.3

COPY environment.yml .
RUN conda env create -f environment.yml

SHELL ["conda", "run", "-n", "dvc", "/bin/bash", "-c"]

# install sagemaker-experiments since it is not available in conda env
RUN pip install sagemaker-experiments
