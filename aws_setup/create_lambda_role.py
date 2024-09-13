import boto3
import json

def create_lambda_role():
    iam_client = boto3.client('iam')

    trust_policy = json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }]
    })

    role_name = 'LambdaS3ExecutionRole'

    try:
        # Check if the role already exists
        print("Fetching role ARN...")
        role = iam_client.get_role(RoleName=role_name)
        role_arn = role['Role']['Arn']
        print("Role ARN fetched.")
        return role_arn

    except iam_client.exceptions.NoSuchEntityException:
        # If the role doesn't exist, create it
        print("Role ARN not found... Generating Role...")
        response = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=trust_policy,
            Description='Role for Lambda to access S3'
        )
        role_arn = response['Role']['Arn']
        print("Role created successfully. Done.")
        return role_arn

    except Exception as e:
        # Handle unexpected errors and print the message
        print(f"Error: {e}")
        raise e