import boto3
import json
import zipfile
import os

lanbda_handshake = boto3.client('lambda')

import boto3
import json
import os

# Accept comma-separated zip file names from the user
lambda_zip_files = input('Input names of zip files containing functions, separated by commas: ')

role_name = 'LambdaS3ExecutionRole'

try:
    print("Fetching role ARN...")
    role = iam_client.get_role(RoleName=role_name)
    role_arn = role['Role']['Arn']
    print("Role ARN fetched.")
    print(role_arn)


# Function to read multiple zip filesaa,
def read_multiple_zip_files(zip_files_input):
    # Split the input string by commas to get individual file names
    zip_file_list = zip_files_input.split(',')
    zip_contents = []

    # Loop through each file, read the contents, and append to the list
    for zip_file_name in zip_file_list:
        zip_file_name = zip_file_name.strip()  # Strip any extra whitespace
        with open(zip_file_name, 'rb') as f:
            zip_contents.append(f.read())

    return zip_contents
def read_zip_file(file_name):
    with open(file_name, 'rb') as f:
        return f.read()