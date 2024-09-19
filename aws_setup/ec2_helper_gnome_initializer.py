import boto3
from botocore.exceptions import ClientError

ec2_client = boto3.client('ec2')
iam_client = boto3.client('iam')


def create_helper_gnome_ssm_role():
    role_name = 'HelperGnomeSSMRole'
    try:
        iam_client.get_role(RoleName=role_name)
        print(f"The Helper Gnome already has his uniform, {role_name}.")
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchEntity':
            print(f"Sewing uniform for the Helper Gnome...")
            try:
                trust_policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {
                                "Service": "ec2.amazonaws.com"
                            },
                            "Action": "sts:AssumeRole"
                        }
                    ]
                }
                iam_client.create_role(
                    RoleName=role_name,
                    AssumeRolePolicyDocument=str(trust_policy),
                    Description='Role for Helper Gnome EC2 SSM access'
                )

                iam_client.attach_role_policy(
                    RoleName=role_name,
                    PolicyArn='arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore'
                )

                print(f"Uniform '{role_name}' Sewn and given to the Helper Gnome")

    except ClientError as e:
        print(f"Error creating role: {e}")


def create_ec2_instance():
    try:
        response = ec2_client.run_instances(
            ImageId='******',
            InstanceType='t2.micro',
            MinCount=1,
            MaxCount=1,
            IamInstanceProfile={'Name': 'HelperGnomeSSMRole'},
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': [{'Key': 'Name', 'Value': 'HelperGnomeInstance'}]
                }
            ],
            UserData='''#!/bin/bash
                              sudo yum update -y
                              sudo yum install -y python3
                              sudo yum install -y aws-cli
                              sudo yum install -y amazon-ssm-agent
                              sudo systemctl start amazon-ssm-agent
                              sudo systemctl enable amazon-ssm-agent
                           '''
        )

        instance_id = response['Instances'][0]['InstanceId']
        print(f"Helper Gnome birthed successfully, his name is {instance_id}")

    except ClientError as e:
        print(f"Error creating EC2 instance: {e}")
