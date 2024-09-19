import boto3
from botocore.exceptions import ClientError

# This will ensure you are using admin credentials to run the script
def is_admin_user():
    """Check if the current user has the IAM permissions to create roles."""
    try:
        iam_client = boto3.client('iam')
        # Attempt to list roles (this requires admin-level permissions)
        iam_client.list_roles()
        print("Admin privileges confirmed.")
        return True
    except ClientError as e:
        print("Insufficient privileges. You must be an admin to create roles.")
        return False

def check_if_role_exists(role_name):
    """Check if the IAM role already exists."""
    try:
        iam_client.get_role(RoleName=role_name)
        print(f"Role '{role_name}' already exists.")
        return True
    except iam_client.exceptions.NoSuchEntityException:
        return False
    except ClientError as e:
        print(f"Error checking for role: {e}")
        return False

def create_or_update_ec2_service_role(role_name, bucket_name, queue_arn):
    """Create or update IAM role for EC2 with both S3 and SQS access."""
    if check_if_role_exists(role_name):
        print(f"Role '{role_name}' exists. Skipping creation or updating policy.")
        # Here you can update the policy if needed
        return

    policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:ListBucket"
                ],
                "Resource": [
                    f"arn:aws:s3:::{bucket_name}",
                    f"arn:aws:s3:::{bucket_name}/*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "sqs:ReceiveMessage",
                    "sqs:DeleteMessage"
                ],
                "Resource": queue_arn
            }
        ]
    }

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

    try:
        # Create the IAM role with EC2 trust policy
        response = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Tags=[
                {
                    'Key': 'Project',
                    'Value': 'PhotoProject'
                }
            ]
        )

        # Attach the combined S3 and SQS access policy
        iam_client.put_role_policy(
            RoleName=role_name,
            PolicyName=f"{role_name}_S3SQSAccessPolicy",
            PolicyDocument=json.dumps(policy_document)
        )
        print(f"Role '{role_name}' created with S3 bucket '{bucket_name}' and SQS queue access.")
        return response['Role']['Arn']
    except ClientError as e:
        print(f"Error creating role: {e}")
        return None

def get_s3_bucket_name_from_db(conn):
    """Retrieve the S3 bucket from the SQLite database."""
    cursor = conn.cursor()
    cursor.execute("SELECT Identifier FROM Resources WHERE ResourceType = 'S3'")
    bucket = cursor.fetchone()
    return bucket[0] if bucket else None


def main():
    if not is_admin_user():
        return

    # Continue with role creation process if admin
    role_name = 'PhotoProjectRole'
    assume_role_policy_document = '''
    {
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
    '''  # Trust policy allowing EC2 to assume the role

    # Your role creation logic here

if __name__ == "__main__":
    main()
