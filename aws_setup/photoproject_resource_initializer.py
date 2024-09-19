import boto3
from botocore.exceptions import ClientError
from datetime import datetime
import argparse
import uuid

dynamodb_client = boto3.client('dynamodb')
s3_client = boto3.client('s3')
iam_client = boto3.client('iam')


# **************************************************
# * convert tags response to a dictionary so its not such a pain in the ass *
# **************************************************

def convert_tags_to_dict(tag_set):
    return {tag['Key']: tag['Value'] for tag in tag_set}


# **************************************************
# * Function: check_dynamo_table_exists *
# **************************************************

def check_dynamo_table_exists():
    table_name = "PhotoProjectResources"
    try:
        dynamodb_client.describe_table(TableName=table_name)
        return True
    except dynamodb_client.exceptions.ResourceNotFoundException:
        return False


# **************************************************
# * Function: find_resources_by_tag *
# **************************************************

def find_project_resources():
    found_resources = {}
    duplicate_resources = []

    # Get the list of all S3 buckets
    try:
        response = s3_client.list_buckets()
        s3_buckets = response['Buckets']
    except ClientError as e:
        print(f"Error retrieving S3 buckets: {e}")
        return found_resources

    # Check each S3 bucket for the specific tag "Project: PhotoProject"
    for bucket in s3_buckets:
        bucket_name = bucket['Name']
        try:
            # Get the tagging information for the current bucket
            tagging_response = s3_client.get_bucket_tagging(Bucket=bucket_name)
            tag_set = tagging_response['TagSet']
            bucket_tags = convert_tags_to_dict(tag_set)  # Convert the list of tags to a dictionary
        except ClientError as e:
            print(f"Bucket '{bucket_name}' has no tags or failed to retrieve tags. Error: {e}")
            continue  # Skip this bucket if there's no tagging information

        # Look for the value "PhotoProject" for the "Project" tag
        if bucket_tags.get('Project') == "PhotoProject":
            if 's3' in found_resources:
                duplicate_resources.append(bucket_name)
            else:
                found_resources['s3'] = bucket_name

    # Raise an exception if duplicates are found
    if duplicate_resources:
        raise Exception(f"Duplicate S3 resources found: {duplicate_resources}")

    return found_resources






# **************************************************
# * Function: initialize_all_resources *
# **************************************************


def create_dynamodb_table():
    table_name = "PhotoProjectResources"

    try:
        # Create the DynamoDB table
        dynamodb_client.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'ResourceName', 'KeyType': 'HASH'}  # Partition key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'ResourceName', 'AttributeType': 'S'}  # String type
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )

        # Wait for the table to become active
        dynamodb_client.get_waiter('table_exists').wait(TableName=table_name)
        print(f"DynamoDB table '{table_name}' created successfully.")

    except ClientError as e:
        print(f"Error creating DynamoDB table: {e}")



# **************************************************
# * Function: initialize_all_resources *
# **************************************************


def add_resource_to_dynamodb(resource_type, resource_identifier):
    table_name = "PhotoProjectResources"  # Hardcoded table name

    try:
        # Add a resource to the DynamoDB table
        dynamodb_client.put_item(
            TableName=table_name,
            Item={
                'ResourceType': {'S': resource_type},  # Partition key (Resource Name)
                'ResourceIdentifier': {'S': resource_identifier},  # ARN of the resource
                'CreationDate': {'S': datetime.now().isoformat()}  # Current timestamp
            }
        )
        print(f"Resource '{resource_type}'{resource_identifier} added to DynamoDB.")

    except ClientError as e:
        print(f"Error adding resource to DynamoDB: {e}")


# **************************************************
# * Function: initialize_all_resources *
# **************************************************

def create_s3_bucket():
    # Generate a unique bucket name using a UUID
    bucket_name = f"photo-project-{uuid.uuid4()}"

    try:
        # Create the S3 bucket
        s3_client.create_bucket(Bucket=bucket_name)
        print(f"S3 bucket '{bucket_name}' created successfully.")

        # Adding the "Project: PhotoProject" tag to the bucket
        s3_client.put_bucket_tagging(
            Bucket=bucket_name,
            Tagging={
                'TagSet': [
                    {'Key': 'Project', 'Value': 'PhotoProject'}
                ]
            }
        )
        print(f"Tag 'Project: PhotoProject' added to bucket '{bucket_name}'.")

        # Return the bucket name
        return bucket_name

    except ClientError as e:
        print(f"Error creating S3 bucket: {e}")
        return None


# **************************************************
# * Function: initialize_all_resources *
# **************************************************

def initialize_all_resources():
    # Check if DynamoDB table exists
    table_name = "ResourceTrackingTable"
    if check_dynamo_table_exists(table_name):
        raise Exception(f"DynamoDB table '{table_name}' already exists.")

    # Check for resources with project tag
    project_tag = "PhotoProject"
    found_resources = find_resources_by_tag('ProjectName', project_tag)
    if found_resources:
        raise Exception(f"Resources with tag 'ProjectName: {project_tag}' already exist: {found_resources}")

    print("No existing resources found. Initializing new resources...")

    # Initialize DynamoDB table
    # Logic to create DynamoDB table and insert ARN tracking

    # Initialize S3 bucket
    if 's3' not in found_resources:
        print("No S3 bucket found, creating one...")
        bucket_name = create_s3_bucket()
        if bucket_name:
            add_resource_to_dynamodb('S3Bucket', bucket_name)
    else:
        print(f"S3 bucket '{found_resources['s3']}' already exists.")

    # Initialize IAM roles
    # Logic to create IAM roles and attach policies


# **************************************************
# * Main Execution *
# **************************************************

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manage AWS resources for the project.")
    parser.add_argument('--overwrite-all', action='store_true', help='Overwrite all resources with new versions.')
    parser.add_argument('--list-arns', action='store_true', help='List ARNs of all project resources.')
    parser.add_argument('--fix-connections', action='store_true',
                        help='Fix connections by adding tagged ARNs to DynamoDB.')
    parser.add_argument('--remove-all', action='store_true', help='Remove all resources, including DynamoDB and S3.')

    args = parser.parse_args()

    if args.overwrite_all:
        handle_overwrite_all()

    if args.list_arns:
        list_arns('ProjectName', 'PhotoProject')

    if args.fix_connections:
        fix_connections()

    if args.remove_all:
        remove_all_resources()

    # Default behavior: Initialize everything, throw exception if resources exist
    if not any(vars(args).values()):  # If no arguments were passed
        initialize_all_resources()
