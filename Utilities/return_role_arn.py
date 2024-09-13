import boto3
from aws_setup.create_lambda_role import create_lambda_role  # Import the function

# Initialize boto3 IAM client
iam_client = boto3.client('iam')

role_name = input('Enter the role name you need an ARN for: ')

try:
    print("Fetching role ARN...")
    role = iam_client.get_role(RoleName=role_name)
    role_arn = role['Role']['Arn']
    print("Role ARN fetched.")
    print(role_arn)

except iam_client.exceptions.NoSuchEntityException:
    # Role not found, ask the user if they want to create it
    create_role = input('Role not found. Would you like to create the role now? Y/N: ').strip().upper()

    if create_role == 'Y':
        # Call the create_lambda_role function
        new_role_arn = create_lambda_role()
        print(f"New Role ARN: {new_role_arn}")
    else:
        print("Role creation aborted.")
except Exception as e:
    print(f"An error occurred: {e}")