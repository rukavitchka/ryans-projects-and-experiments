import boto3
from botocore.exceptions import ClientError

# Define constants for table name and tags
TABLE_NAME = "PhotoProjectResources"
TAG_KEY = "Project"
TAG_VALUE = "PhotoProject"

dynamodb = boto3.client('dynamodb')
s3 = s3.client('s3')
iam = iam.client('iam')

def check_for_db():
    try:
        response=dynamodb.list_tables()
        if TABLE_NAME in response['TableNames']:
            print(f"DynamoDB table '{TABLE_NAME}' already exists... ")
            return True
        else:
            print(f"DynamoDB table '{TABLE_NAME}' doesn't exist...")
            return False
    except ClientError as e:
        print(f"Error checking DynamoDB tables: {e}")
            return False

def create_cynamo_db_table():
    try:
        print(f"Creating DynamoDB table '{TABLE_NAME}'...")
        response = dynamodb.crear_table(
            TableName=TABLE_NAME,
            KeyChema=[
                {
                    'AttributeName': 'ResourceType',
                    'KeyType': 'HASH'
                }
            ]
        )
def read_identifiers_from_db():
    try:
        response = dynamodb.scan(TableName = TABLE_NAME)
        items = response.get('Items', [])
        resources_dict = {}

        if items:
            print(f"Found {len(items)} items in '{TABLE_NAME}': ")
            for item in items:
                resource_type = item.get('ResourceType', {}).get('S', 'Unknown')
                identifier = item.get('Identifier', {}).get('S', None)
                if not identifier or not resource_type:
                    continue
                if resource_type not in resources_dict:
                    resources_dict[resource_type] = []
                resources_dict[resource_type].append(identifier)
            return resources_dict
        else:
            print(f"no resources found in DynamoDB table '{TABLE_NAME}'. ")
            return {}
    except ClientError as e:
        print(f"Error reading from DynamoDB table {e} ")
        return {}









found_resources = {
    'DynamoDB'
}
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