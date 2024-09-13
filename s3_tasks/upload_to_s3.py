import boto3
import random
import re
import json
import os
import uuid
import botocore
import argparse


alphanum = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
db_file = 'filename_mapping.json'

# ---------------------------------------------------
# Utility Functions
# ---------------------------------------------------

# ***************************************************
# Initialize the JSON file if it does not exist
# ***************************************************
def initialize_json():
    """Initialize the JSON file with bucket_name and an empty used_ids list."""
    if not os.path.exists(db_file):
        print(f"{db_file} not found. Initializing it now.")
        filename_mapping = {
            'bucket_name': '',  # Initialize as an empty string
            'used_ids': []  # Initialize as an empty list
        }
        save_filename_mapping(filename_mapping)
        print(f"Initialized {db_file} with bucket_name and used_ids.")
    else:
        print(f"{db_file} already exists. No need to initialize.")

# ***************************************************
# Load filename mapping from JSON
# ***************************************************
def load_filename_mapping():
    """Loads the filename mapping data from the JSON file."""
    with open(db_file, 'r') as file:
        filename_mapping = json.load(file)
        # Convert 'used_ids' to a set for efficient operations
        filename_mapping['used_ids'] = set(filename_mapping.get('used_ids', []))
    return filename_mapping

# ***************************************************
# Save filename mapping to JSON
# ***************************************************
def save_filename_mapping(mapping):
    """Saves the filename mapping data to the JSON file."""
    # Convert 'used_ids' back to a list for JSON serialization
    mapping['used_ids'] = list(mapping['used_ids'])
    with open(db_file, 'w') as file:
        json.dump(mapping, file)

# ---------------------------------------------------
# S3 Bucket Management Functions
# ---------------------------------------------------

# ***************************************************
# Check if the S3 bucket exists, otherwise create it
# ***************************************************
def check_or_create_bucket():
    """Check or create the S3 bucket."""
    filename_mapping = load_filename_mapping()  # Load the filename mapping from JSON
    s3_handshake = boto3.client('s3')  # Connect to S3
    bucket_name = filename_mapping['bucket_name']  # Check if a bucket name is stored in the mapping

    # If there's already a bucket name in the mapping, check if the bucket exists in S3
    if bucket_name:
        response = s3_handshake.list_buckets()
        for bucket in response['Buckets']:
            if bucket['Name'] == bucket_name:
                print(f"Bucket '{bucket_name}' already exists.")
                return bucket_name  # Reuse the existing bucket

    # If no bucket exists in the mapping or the bucket is not found in S3, create a new one
    bucket_name = f"war-in-pocket-{uuid.uuid4()}"  # Create a new unique bucket name
    s3_handshake.create_bucket(Bucket=bucket_name)  # Create the bucket in S3
    print(f"Bucket created: {bucket_name}")

    # Store the new bucket name in the mapping
    filename_mapping['bucket_name'] = bucket_name
    save_filename_mapping(filename_mapping)  # Save the updated mapping

    return bucket_name  # Return the bucket name

# ***************************************************
# List S3 objects
# ***************************************************
def list_s3_objects():
    """List objects in the S3 bucket."""
    filename_mapping = load_filename_mapping()  # Ensure you're working with the latest mapping
    try:
        s3_handshake = boto3.client('s3')
        response = s3_handshake.list_objects_v2(Bucket=filename_mapping['bucket_name'])
        if 'Contents' in response:
            print("Files in the bucket:")
            for obj in response['Contents']:
                print(obj['Key'])
        else:
            print("The bucket is empty or does not exist.")
    except botocore.exceptions.ClientError as e:
        print(f"Error listing files: {e.response['Error']['Message']}")
    except Exception as e:
        print(f"An error occurred: {e}")

# ---------------------------------------------------
# Filename Management Functions
# ---------------------------------------------------

# ***************************************************
# Get file extension from filename
# ***************************************************
def get_file_extension(filename):
    """Get the file extension from the given filename."""
    match = re.search(r'\.[a-zA-Z0-9]+$', filename)
    return match.group() if match else ''

# ***************************************************
# Generate a random filename
# ***************************************************
def generate_random_filename(filename):
    """Generate a random filename with a suffix if needed."""
    filename_mapping = load_filename_mapping()  # Load the latest mapping
    suffix = 0
    if filename in filename_mapping:
        random_id = filename_mapping[filename][0].rsplit('-', 1)[0]
        while f'{random_id}-{suffix}{get_file_extension(filename)}' in filename_mapping[filename]:
            suffix += 1
    else:
        random_id = ''.join(random.sample(alphanum, 2))
        while random_id in filename_mapping['used_ids']:
            random_id = ''.join(random.sample(alphanum, 2))
    filename_mapping['used_ids'].add(random_id)
    save_filename_mapping(filename_mapping)  # Save the updated mapping

    new_filename = f'{random_id}-{suffix}{get_file_extension(filename)}'
    return new_filename

# ---------------------------------------------------
# File Upload Functions
# ---------------------------------------------------

# ***************************************************
# Upload a file to S3
# ***************************************************
def upload_file_to_s3(filename):
    """Upload a file to S3 and update the filename mapping."""
    filename_mapping = load_filename_mapping()  # Load the mapping once at the start
    s3_handshake = boto3.client('s3')

    # Generate a new filename before attempting the upload
    new_filename = generate_random_filename(filename)

    try:
        # Ensure the bucket exists before uploading
        check_or_create_bucket()

        # Upload the file to S3 with the generated filename
        s3_handshake.upload_file(
            filename,
            filename_mapping['bucket_name'],
            new_filename
        )

        # Update filename_mapping only after a successful upload
        if filename not in filename_mapping:
            filename_mapping[filename] = []
        filename_mapping[filename].append(new_filename)
        save_filename_mapping(filename_mapping)  # Save the updated mapping

        print(f"File {filename} uploaded successfully as {new_filename}.")

    except botocore.exceptions.ClientError as e:
        print(f"Upload failed: {e.response['Error']['Message']}")
    except Exception as e:
        print(f"An error occurred: {e}")

    list_s3_objects()  # No need to save mapping again

# ---------------------------------------------------
# Main Execution
# ---------------------------------------------------

if __name__ == '__main__':
    # Argument parsing and execution for when the script is run directly
    parser = argparse.ArgumentParser(description='Upload a file to S3')
    parser.add_argument('filename', help='Your file\'s path')
    args = parser.parse_args()
    filename = args.filename

    # Initialize the JSON file and start the upload process
    initialize_json()
    upload_file_to_s3(filename)
