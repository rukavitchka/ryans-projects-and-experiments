from moto import mock_aws


@mock_aws
def test_s3():
    import boto3
    s3 = boto3.client('s3', region_name='us-east-1')

    # Create a mock S3 bucket
    s3.create_bucket(Bucket='my-mock-bucket')

    # List the buckets to verify
    response = s3.list_buckets()
    print(response['Buckets'])


# Run the test
test_s3()
