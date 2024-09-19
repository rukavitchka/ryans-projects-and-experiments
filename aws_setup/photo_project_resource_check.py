#from moto import mock_s3, mock_secretsmanager, mock_iam, mock_resourcegroupstaggingapi
from moto import mock_aws
# Mock all AWS services before running the script logic
#mock_s3().start()
#mock_secretsmanager().start()
#mock_iam().start()
#mock_resourcegroupstaggingapi().start()
mock_aws().start()

# Your existing script below this point remains unchanged
import os
import sqlite3
import boto3
import shutil
from botocore.exceptions import ClientError
import uuid
from cryptography.fernet import Fernet

DB_NAME = "warinpocket.sqlite"
LOCAL_DB_PATH = f"/Users/renncollins/PycharmProjects/PhotoProject/{DB_NAME}"
secret_name = "photo_project_encryption_key"

s3_client = boto3.client('s3')
resource_client = boto3.client('resourcegroupstaggingapi')

#**********************************************************************
# Function List (Ordered by Call Sequence)
#**********************************************************************
# check_s3_bucket_exists() -> str or None: Lists all S3 buckets with the specific prefix and returns the first one.
# check_local_db() -> bool: Checks if the local SQLite database exists.
# create_s3_bucket() -> str or None: Creates a new S3 bucket and returns the bucket name.
# upload_db_to_s3_bucket(bucket_name: str): Uploads the local SQLite database to the specified S3 bucket.
# load_db() -> sqlite3.Connection or None: Loads the local SQLite database if it exists.
# check_db_in_s3_bucket(bucket_name: str) -> bool: Checks if the SQLite database exists in the specified S3 bucket.
# download_db_from_s3(bucket_name: str): Downloads the SQLite database from the specified S3 bucket.
# create_new_photo_project_db() -> sqlite3.Connection or None: Creates a new SQLite database for the Photo Project.
# insert_s3_bucket_into_db(conn: sqlite3.Connection, bucket_name: str): Inserts the S3 bucket name into the SQLite database.
# get_s3_bucket_name_from_db(conn: sqlite3.Connection) -> str or None: Retrieves the S3 bucket name from the SQLite database.
# check_db_specified_bucket_exists(conn: sqlite3.Connection) -> bool: Checks if the S3 bucket exists in AWS.
# search_for_photo_project_resources(): Searches for all AWS resources tagged 'PhotoProject' and prints them.

#**********************************************************************
# Check if S3 bucket exists with the specific prefix
#**********************************************************************
def check_s3_bucket_exists():
    """List all S3 buckets with the prefix 'warinpocketbucket-' and return the first one."""
    prefix = "warinpocketbucket-"
    try:
        response = s3_client.list_buckets()
        for bucket in response['Buckets']:
            if bucket['Name'].startswith(prefix):
                print(f"Found bucket '{bucket['Name']}' with prefix '{prefix}'.")
                return bucket['Name']
        print(f"No bucket found with prefix '{prefix}'.")
        return None
    except ClientError as e:
        print(f"Error listing buckets: {e}")
        return None




#**********************************************************************
# encrypt the database
#**********************************************************************
def encrypt_file(source_file_path, encrypted_file_path, key):
    """Encrypt the source file and save the encrypted content to a separate file."""
    fernet = Fernet(key)

    with open(source_file_path, 'rb') as file:
        original = file.read()  # Read the original file

    encrypted = fernet.encrypt(original)  # Encrypt the file

    with open(encrypted_file_path, 'wb') as encrypted_file:
        encrypted_file.write(encrypted)  # Write the encrypted content to the new file

    print(f"File '{source_file_path}' encrypted and saved as '{encrypted_file_path}'.")
#**********************************************************************
# Check if S3 bucket exists with the specific prefix
#**********************************************************************




def create_and_store_key_in_secrets_manager(secret_name):
    """Generate a new encryption key and store it in AWS Secrets Manager if it doesn't already exist."""
    secrets_client = boto3.client('secretsmanager')

    # Check if the secret already exists
    try:
        # Try to retrieve the secret to see if it exists
        response = secrets_client.get_secret_value(SecretId=secret_name)
        print(f"Encryption key already exists in Secrets Manager under secret name '{secret_name}'.")
        return response['SecretString'].encode()
    except secrets_client.exceptions.ResourceNotFoundException:
        # If the secret doesn't exist, generate a new encryption key
        key = Fernet.generate_key()
        print(f"Generated a new encryption key: {key.decode()}")

        # Store the new key in Secrets Manager
        try:
            secrets_client.create_secret(
                Name=secret_name,
                SecretString=key.decode()  # Store the key as a string
            )
            print(f"Encryption key successfully stored in Secrets Manager under secret name '{secret_name}'.")
            return key
        except ClientError as e:
            print(f"Error storing encryption key in Secrets Manager: {e}")
            return None
    except ClientError as e:
        print(f"Error retrieving secret from Secrets Manager: {e}")
        return None

#**********************************************************************
# copy db before encryption
#**********************************************************************
def copy_db():
    """Copy the database file to a new location."""
    try:
        shutil.copy(LOCAL_DB_PATH, f"{LOCAL_DB_PATH}_copy")
        print(f"Database copied from '{LOCAL_DB_PATH}' to '{LOCAL_DB_PATH}_copy'.")
    except Exception as e:
        print(f"Error copying the database: {e}")



#**********************************************************************
# Check if the local SQLite database exists
#**********************************************************************
def check_local_db():
    if os.path.exists(LOCAL_DB_PATH):
        print(f"Database '{DB_NAME}' found locally.")
        return True
    else:
        print(f"Database '{DB_NAME}' not found locally.")
        return False

#**********************************************************************
# Create a new S3 bucket
#**********************************************************************
def create_s3_bucket():
    bucket_name = f"warinpocketbucket-{uuid.uuid4()}"
    #current_region = boto3.session.Session().region_name
    try:
        s3_client.create_bucket(
            Bucket=bucket_name,
            #CreateBucketConfiguration={'LocationConstraint': current_region}
        )

        s3_client.put_bucket_tagging(
            Bucket=bucket_name,
            Tagging={
                'TagSet': [
                    {
                        'Key': 'Project',
                        'Value': 'PhotoProject'
                    }
                ]
            }
        )

        print(f"New Bucket '{bucket_name}' created in us-east-1.")
        return bucket_name
    except ClientError as e:
        print(f"Error creating bucket: {e}")
        return None

#**********************************************************************
# Upload SQLite database to S3 bucket
#**********************************************************************
def upload_db_to_s3_bucket(conn):
    """Encrypt a copy of the SQLite database and upload it to the specified S3 bucket."""
    # Use the correct secret name as a string
    key = create_and_store_key_in_secrets_manager("db_encryption_key_photo_project")
    encrypted_db_path = f"{LOCAL_DB_PATH}_copy"  # The temporary encrypted copy path

    # Retrieve the S3 bucket name from the database
    bucket_name = get_s3_bucket_name_from_db(conn)

    # Check if the bucket name was retrieved successfully
    if not bucket_name:
        print("Error: S3 bucket name not found in the database.")
        return

    if key:
        # Step 1: Copy the database
        copy_db()  # This will create the _copy version of the DB

        # Step 2: Encrypt the copied database
        encrypt_file(encrypted_db_path, encrypted_db_path, key)

        try:
            # Step 3: Upload the encrypted copy to S3 with the original filename
            s3_client.upload_file(encrypted_db_path, bucket_name, DB_NAME)
            print(f"Encrypted database '{DB_NAME}' uploaded to S3 bucket '{bucket_name}'.")

            # Step 4: Remove the encrypted copy after upload
            os.remove(encrypted_db_path)
            print(f"Encrypted file '{encrypted_db_path}' deleted after upload.")
        except ClientError as e:
            print(f"Error uploading database to S3: {e}")
    else:
        print("Error: Encryption key not found or created.")
#**********************************************************************
# Load the local SQLite database
#**********************************************************************
def load_db():
    """Load the local SQLite database if it exists."""
    if check_local_db():
        try:
            conn = sqlite3.connect(LOCAL_DB_PATH)
            return conn
        except sqlite3.Error as e:
            print(f"Error connecting to sqlite: {e}")
            return None
    return None

#**********************************************************************
# Check if SQLite database exists in the specified S3 bucket
#**********************************************************************
def check_db_in_s3_bucket(bucket_name):
    """Check if the SQLite database is present in the specified S3 bucket."""
    try:
        s3_client.head_object(Bucket=bucket_name, Key=DB_NAME)
        print(f"Database '{DB_NAME}' exists in S3 bucket '{bucket_name}'.")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            print(f"Database '{DB_NAME}' not found in S3 bucket '{bucket_name}'.")
            return False
        else:
            print(f"Error checking database in S3: {e}")
            return False

#**********************************************************************
# Download SQLite database from S3 bucket
#**********************************************************************
def download_db_from_s3(bucket_name):
    try:
        s3_client.download_file(bucket_name, DB_NAME, LOCAL_DB_PATH)
        print(f"Database downloaded to {LOCAL_DB_PATH}")
    except ClientError as e:
        print(f"Error downloading from S3: {e}")

#**********************************************************************
# Create a new SQLite database for the Photo Project
#**********************************************************************
def create_new_photo_project_db():
    """Create a new SQLite database for the Photo Project."""
    try:
        print(f"Attempting to create a new SQLite database at {LOCAL_DB_PATH}")
        conn = sqlite3.connect(LOCAL_DB_PATH)
        cursor = conn.cursor()
        print("Creating new database...")

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Resources (
                ResourceType TEXT NOT NULL,
                Identifier TEXT NOT NULL
            )
        ''')

        conn.commit()
        print(f"Database '{DB_NAME}' created with necessary tables.")
        return conn
    except sqlite3.Error as e:
        print(f"Error creating SQLite database: {e}")
        return None


#**********************************************************************
# Insert the new S3 bucket into the SQLite database
#**********************************************************************
def insert_s3_bucket_into_db(conn, bucket_name):
    """Insert the new S3 bucket into the SQLite database."""
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Resources (ResourceType, Identifier) VALUES (?, ?)", ('S3', bucket_name))
        conn.commit()
        print(f"S3 bucket '{bucket_name}' inserted into the database.")
    except sqlite3.Error as e:
        print(f"Error inserting S3 bucket into the database: {e}")

#**********************************************************************
# Retrieve the S3 bucket name from the SQLite database
#**********************************************************************
def get_s3_bucket_name_from_db(conn):
    """Retrieve the S3 bucket from the SQLite database."""
    cursor = conn.cursor()
    cursor.execute("SELECT Identifier FROM Resources WHERE ResourceType = 'S3'")
    bucket = cursor.fetchone()
    return bucket[0] if bucket else None

#**********************************************************************
# Check if the S3 bucket exists in AWS
#**********************************************************************
def check_db_specified_bucket_exists(conn):
    """Check if the S3 bucket exists in AWS."""
    bucket_name = get_s3_bucket_name_from_db(conn)

    if bucket_name:
        try:
            s3_client.head_bucket(Bucket=bucket_name)
            print(f"S3 bucket '{bucket_name}' exists.")
            return True
        except ClientError:
            print(f"The S3 bucket '{bucket_name}' is missing.")
            return False
    else:
        print("No S3 bucket found in the database.")
        return False

#**********************************************************************
# Search for all AWS resources tagged 'PhotoProject'
#**********************************************************************
def search_for_photo_project_resources():
    """Search for all AWS resources tagged with 'PhotoProject' and print them."""
    try:
        response = resource_client.get_resources(
            TagFilters=[{'Key': 'Project', 'Values': ['PhotoProject']}]
        )
        resources = response.get('ResourceTagMappingList', [])
        if resources:
            print("Resources tagged with 'PhotoProject':")
            for resource in resources:
                print(f"- {resource['ResourceARN']}")
        else:
            print("No resources found with the 'PhotoProject' tag.")
    except ClientError as e:
        print(f"Error retrieving tagged resources: {e}")

#**********************************************************************
# MAIN LOGIC
#**********************************************************************
bucket_name = check_s3_bucket_exists()
local_db_exists = check_local_db()  # Store the result of checking local DB existence
conn = None  # Initialize connection variable

if local_db_exists and not bucket_name:
    # Case 1: Local DB exists, but no S3 bucket
    print("Local DB exists, but no S3 bucket found.")
    bucket_name = create_s3_bucket()
    conn = load_db()  # Load the local DB into 'conn'
    upload_db_to_s3_bucket(conn)  # Upload the local DB to the new S3 bucket

elif local_db_exists and bucket_name:
    # Case 2: Local DB exists and S3 bucket exists
    print("Local DB and S3 bucket both exist.")
    conn = load_db()  # Load the local DB into 'conn'
    if not check_db_in_s3_bucket(bucket_name):  # If DB is not in the S3 bucket
        upload_db_to_s3_bucket(conn)  # Upload the local DB to the S3 bucket

elif not local_db_exists and bucket_name:
    # Case 3: No local DB, but S3 bucket exists
    print("No local DB, but S3 bucket found.")
    if check_db_in_s3_bucket(bucket_name):  # If DB is in the S3 bucket
        download_db_from_s3(bucket_name)  # Download the DB from S3
        conn = load_db()  # Load the downloaded DB into 'conn'
    else:
        print("No DB found in S3, creating a new one locally.")
        conn = create_new_photo_project_db()
        upload_db_to_s3_bucket(conn)  # Upload the new DB to the S3 bucket
else:
    # Case 4: No local DB and no S3 bucket
    print("Neither local DB nor S3 bucket found. Creating both.")
    bucket_name = create_s3_bucket()
    conn = create_new_photo_project_db()
    upload_db_to_s3_bucket(conn)

# Search and print AWS resources tagged 'PhotoProject'
search_for_photo_project_resources()