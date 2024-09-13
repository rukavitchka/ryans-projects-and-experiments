import boto3

# Initialize boto3 STS client
sts_client = boto3.client('sts')

# Call the STS get-caller-identity API
response = sts_client.get_caller_identity()

# Extract and print the account ID
account_id = response['Account']
print(f"AWS Account ID: {account_id}")
