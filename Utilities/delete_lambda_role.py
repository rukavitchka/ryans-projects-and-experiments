import boto3

def delete_lambda_role(role_name):
    iam_client = boto3.client('iam')

    try:
        # Delete the role
        iam_client.delete_role(RoleName=role_name)
        print(f"Role '{role_name}' deleted successfully.")
    except iam_client.exceptions.NoSuchEntityException:
        print(f"Role '{role_name}' not found.")
    except Exception as e:
        print(f"Error deleting role: {e}")