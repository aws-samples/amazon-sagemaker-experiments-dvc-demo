# Bring-your-own Algorithm Sample

This example shows how to package an algorithm for use with SageMaker. We have chosen a simple [CatBoost][catboost] implementation of regression to illustrate the procedure.

SageMaker supports two execution modes: _training_ where the algorithm uses input data to train a new model and _serving_ where the algorithm accepts HTTP requests and uses the previously trained model to do an inference (also called "scoring", "prediction", or "transformation").

The algorithm that we have built here supports both training and scoring in SageMaker with the same container image. It is perfectly reasonable to build an algorithm that supports only training _or_ scoring as well as to build an algorithm that has separate container images for training and scoring.v

In order to build a production grade inference server into the container, we use the following stack to make the implementer's job simple:

1. __[nginx][nginx]__ is a light-weight layer that handles the incoming HTTP requests and manages the I/O in and out of the container efficiently.
2. __[gunicorn][gunicorn]__ is a WSGI pre-forking worker server that runs multiple copies of your application and load balances between them.
3. __[flask][flask]__ is a simple web framework used in the inference app that you write. It lets you respond to call on the `/ping` and `/invocations` endpoints without having to write much code.

## The Structure of the Sample Code

The components are as follows:

* __Dockerfile__: The _Dockerfile_ describes how the image is built and what it contains. It is a recipe for your container and gives you tremendous flexibility to construct almost any execution environment you can imagine. Here. we use the Dockerfile to describe a pretty standard python science stack and the simple scripts that we're going to add to it. See the [Dockerfile reference][dockerfile] for what's possible here.

* __catboost_regressor__: The directory that contains the application to run in the container. See the next session for details about each of the files.

### The application run inside the container

When SageMaker starts a container, it will invoke the container with an argument of either __train__ or __serve__. We have set this container up so that the argument in treated as the command that the container executes. When training, it will run the __train__ program included and, when serving, it will run the __serve__ program.

* __train__: The main program for training the model. When you build your own algorithm, you'll edit this to include your training code.
* __serve__: The wrapper that starts the inference server. In most cases, you can use this file as-is.
* __wsgi.py__: The start up shell for the individual server workers. This only needs to be changed if you changed where predictor.py is located or is named.
* __predictor.py__: The algorithm-specific inference server. This is the file that you modify with your own algorithm's code.
* __nginx.conf__: The configuration for the nginx master server that manages the multiple workers.

[catboost]: https://catboost.ai/ "CatBoost Home Page"
[dockerfile]: https://docs.docker.com/engine/reference/builder/ "The official Dockerfile reference guide"
[ecr]: https://aws.amazon.com/ecr/ "ECR Home Page"
[nginx]: http://nginx.org/
[gunicorn]: http://gunicorn.org/
[flask]: http://flask.pocoo.org/
