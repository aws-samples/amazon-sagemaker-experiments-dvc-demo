import setuptools


setuptools.setup(
    name="sagemakerStudioCDK",
    version="0.0.1",

    description="aws-cdk-sagemaker-studio",

    author="frpaolo",

    package_dir={"": "sagemakerStudioCDK"},
    packages=setuptools.find_packages(where="sagemakerStudioCDK"),

    install_requires=[
        "aws-cdk.core==1.144.0",
        "aws-cdk.cloudformation_include==1.144.0",
        "aws-cdk.aws_iam==1.144.0",
        "aws-cdk.aws_ec2==1.144.0",
        "aws-cdk.aws_sagemaker==1.144.0",
        "boto3"
    ],

    python_requires=">=3.6",

    classifiers=[
        "Development Status :: 4 - Beta",

        "Intended Audience :: Developers",

        "License :: OSI Approved :: Apache Software License",

        "Programming Language :: JavaScript",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",

        "Topic :: Software Development :: Code Generators",
        "Topic :: Utilities",

        "Typing :: Typed",
    ],
)
