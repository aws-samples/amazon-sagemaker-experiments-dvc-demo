# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from aws_cdk import (
	aws_iam as iam,
	aws_ec2 as ec2,
	aws_sagemaker as sagemaker,
	core
)

sagemaker_arn_region_account_mapping = {
	"eu-west-1": "470317259841",
	"us-east-1": "081325390199",
	"us-east-2": "429704687514",
	"us-west-1": "742091327244",
	"us-west-2": "236514542706",
	"af-south-1": "559312083959",
	"ap-east-1": "493642496378",
	"ap-south-1": "394103062818",
	"ap-northeast-2": "806072073708",
	"ap-southeast-1": "492261229750",
	"ap-southeast-2": "452832661640",
	"ap-northeast-1": "102112518831",
	"ca-central-1": "310906938811",
	"eu-central-1": "936697816551",
	"eu-west-2": "712779665605",
	"eu-west-3": "615547856133",
	"eu-north-1": "243637512696",
	"eu-south-1": "592751261982",
	"sa-east-1": "782484402741",
}


class SagemakerStudioStack(core.Stack):

	def __init__(self, scope: core.Construct, construct_id: str, domain_id: str, **kwargs) -> None:
		super().__init__(scope, construct_id, **kwargs)
		
		# Create a SageMaker
		role_sagemaker_studio_domain = iam.Role(
			self,
			'RoleForSagemakerStudioUsers',
		    assumed_by=iam.CompositePrincipal(
		    	iam.ServicePrincipal('sagemaker.amazonaws.com'),
				iam.ServicePrincipal('codebuild.amazonaws.com'), # needed to use the sm-build command
	    	),
		    role_name="RoleSagemakerStudioUsers",
		    managed_policies=[
				iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSageMakerFullAccess"),
				iam.ManagedPolicy.from_aws_managed_policy_name("AWSCodeBuildAdminAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AWSCodeCommitFullAccess")
			],
			inline_policies={
				"s3bucket": iam.PolicyDocument(
    				statements=[
    					iam.PolicyStatement(
    						effect=iam.Effect.ALLOW,
							actions=["s3:ListBucket","s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:PutObjectTagging"],
							resources=["*"]
    					)
    				]
				),
				"sm-build-policy": iam.PolicyDocument(
					statements=[
						iam.PolicyStatement(
							sid="EcrAuthorizationTokenRetrieval",
							effect=iam.Effect.ALLOW,
							actions=[
								"ecr:BatchGetImage",
								"ecr:GetDownloadUrlForLayer"
							],
							resources=[
								"arn:aws:ecr:*:763104351884:repository/*",
				                "arn:aws:ecr:*:217643126080:repository/*",
				                "arn:aws:ecr:*:727897471807:repository/*",
				                "arn:aws:ecr:*:626614931356:repository/*",
				                "arn:aws:ecr:*:683313688378:repository/*",
				                "arn:aws:ecr:*:520713654638:repository/*",
				                "arn:aws:ecr:*:462105765813:repository/*"
							]
						),
						iam.PolicyStatement(
							effect=iam.Effect.ALLOW,
							actions=[
								"ecr:CreateRepository",
								"ecr:BatchGetImage",
								"ecr:CompleteLayerUpload",
								"ecr:DescribeImages",
								"ecr:DescribeRepositories",
								"ecr:UploadLayerPart",
								"ecr:ListImages",
								"ecr:InitiateLayerUpload", 
								"ecr:BatchCheckLayerAvailability",
								"ecr:PutImage"	
							],
							resources=["arn:aws:ecr:*:*:repository/sagemaker-studio*"]
						),
						iam.PolicyStatement(
							effect=iam.Effect.ALLOW,
							actions=[
								"codebuild:DeleteProject",
                				"codebuild:CreateProject",
				                "codebuild:BatchGetBuilds",
				                "codebuild:StartBuild"
							],
							resources=["arn:aws:codebuild:*:*:project/sagemaker-studio*"]
						),
						iam.PolicyStatement(
							effect=iam.Effect.ALLOW,
							actions=["logs:CreateLogStream"],
							resources=["arn:aws:logs:*:*:log-group:/aws/codebuild/sagemaker-studio*"]
						),
						iam.PolicyStatement(
							effect=iam.Effect.ALLOW,
							actions=[
				                "logs:GetLogEvents",
				                "logs:PutLogEvents"							
							],
							resources=["arn:aws:logs:*:*:log-group:/aws/codebuild/sagemaker-studio*:log-stream:*"]
						),
						iam.PolicyStatement(
							effect=iam.Effect.ALLOW,
							actions=[
								"logs:CreateLogGroup"
							],
							resources=["*"]
						),
						iam.PolicyStatement(
							effect=iam.Effect.ALLOW,
							actions=["ecr:GetAuthorizationToken"],
							resources=["*"]
						),
						iam.PolicyStatement(
							effect=iam.Effect.ALLOW,
							actions=["s3:CreateBucket"],
							resources=["arn:aws:s3:::sagemaker*"]
						),
						iam.PolicyStatement(
							effect=iam.Effect.ALLOW,
							actions=[
								"iam:GetRole",
                				"iam:ListRoles"
                			],
                			resources=["*"]
						),
						iam.PolicyStatement(
							effect=iam.Effect.ALLOW,
							actions=["iam:PassRole"],
							resources=["arn:aws:iam::*:role/*"],
							conditions={
								"StringLikeIfExists":{
									"iam:PassedToService":"codebuild.amazonaws.com"
								}
							}
						)
					]	
				)
			}
		)
		
		cfn_image = sagemaker.CfnImage(
			self,
			"DvcImage",
    		image_name="conda-env-dvc-kernel",
    		image_role_arn=role_sagemaker_studio_domain.role_arn,
		)
		
		cfn_image_version = sagemaker.CfnImageVersion(
			self,
			"DvcImageVersion",
			image_name="conda-env-dvc-kernel",
			base_image="{}.dkr.ecr.{}.amazonaws.com/smstudio-custom:conda-env-dvc-kernel".format(self.account, self.region)
		)
		
		cfn_image_version.add_depends_on(cfn_image)
		
		cfn_app_image_config = sagemaker.CfnAppImageConfig(
			self,
			"DvcAppImageConfig",
    		app_image_config_name="conda-env-dvc-kernel-config",
    		kernel_gateway_image_config=sagemaker.CfnAppImageConfig.KernelGatewayImageConfigProperty(
        		kernel_specs=[
        			sagemaker.CfnAppImageConfig.KernelSpecProperty(
            			name="conda-env-dvc-py",
            			display_name="Python [conda env: dvc]"
        			)
        		],
	        	file_system_config=sagemaker.CfnAppImageConfig.FileSystemConfigProperty(
	            	default_gid=0,
	            	default_uid=0,
	            	mount_path="/root"
	        	)
	    	),
		)
		
		cfn_app_image_config.add_depends_on(cfn_image_version)
		
		team = "data-scientist-dvc"
		
		if domain_id is not None:
			my_default_datascience_user = sagemaker.CfnUserProfile(
				self,
				"CfnUserProfile",
				domain_id=domain_id,
				user_profile_name=team,
				user_settings=sagemaker.CfnUserProfile.UserSettingsProperty(
			        execution_role=role_sagemaker_studio_domain.role_arn,
			        kernel_gateway_app_settings=sagemaker.CfnUserProfile.KernelGatewayAppSettingsProperty(
			            custom_images=[
			            	sagemaker.CfnUserProfile.CustomImageProperty(
			                	app_image_config_name="conda-env-dvc-kernel-config",
			                	image_name="conda-env-dvc-kernel",
			            	)
			            ]
			        ),
					jupyter_server_app_settings=sagemaker.CfnUserProfile.JupyterServerAppSettingsProperty(
						default_resource_spec=sagemaker.CfnUserProfile.ResourceSpecProperty(
							instance_type="system",
							sage_maker_image_arn="arn:aws:sagemaker:{}:{}:image/jupyter-server-3".format(self.region, sagemaker_arn_region_account_mapping[self.region]),
						)
					),
			    )
			)
			
			my_default_datascience_user.add_depends_on(cfn_app_image_config)
		else:
		
			self.role_sagemaker_studio_domain = role_sagemaker_studio_domain
			self.sagemaker_domain_name = "DomainForSagemakerStudio"
	
			default_vpc_id = ec2.Vpc.from_lookup(
				self,
				"VPC",
			    is_default=True
			)
	
			self.vpc_id = default_vpc_id.vpc_id
			self.public_subnet_ids = [public_subnet.subnet_id for public_subnet in default_vpc_id.public_subnets]
			
			my_sagemaker_domain = sagemaker.CfnDomain(
				self,
				"SageMakerStudioDomain",
			    auth_mode="IAM",
			    default_user_settings=sagemaker.CfnDomain.UserSettingsProperty(
			        execution_role=self.role_sagemaker_studio_domain.role_arn,
			        kernel_gateway_app_settings=sagemaker.CfnDomain.KernelGatewayAppSettingsProperty(
			            custom_images=[
			            	sagemaker.CfnDomain.CustomImageProperty(
			                	app_image_config_name="conda-env-dvc-kernel-config",
			                	image_name="conda-env-dvc-kernel",
			            )]
			        ),
					jupyter_server_app_settings=sagemaker.CfnDomain.JupyterServerAppSettingsProperty(
						default_resource_spec=sagemaker.CfnDomain.ResourceSpecProperty(
							instance_type="system",
							sage_maker_image_arn="arn:aws:sagemaker:{}:{}:image/jupyter-server-3".format(self.region, sagemaker_arn_region_account_mapping[self.region]),
						)
					),
				),
			    domain_name="domain-with-custom-conda-env",
			    subnet_ids=self.public_subnet_ids,
			    vpc_id=self.vpc_id
			)
			
			my_sagemaker_domain.add_depends_on(cfn_app_image_config)
	
			my_default_datascience_user = sagemaker.CfnUserProfile(
				self,
				"CfnUserProfile",
				domain_id=my_sagemaker_domain.attr_domain_id,
				user_profile_name=team,
				user_settings=sagemaker.CfnUserProfile.UserSettingsProperty(
			        execution_role=self.role_sagemaker_studio_domain.role_arn
			    )
			)
			
			core.CfnOutput(
				self,
				"DomainIdSagemaker",
			    value=my_sagemaker_domain.attr_domain_id,
			    description="The sagemaker domain ID",
			    export_name="DomainIdSagemaker"
			)


		core.CfnOutput(
			self,
			f"cfnoutput{team}",
		    value=my_default_datascience_user.attr_user_profile_arn,
		    description="The User Arn TeamA domain ID",
		    export_name=F"UserArn{team}"
		)