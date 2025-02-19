import os
from pydo import Client
import boto3
from dotenv import load_dotenv
from datetime import datetime
import urllib.parse
from requests.utils import requote_uri

load_dotenv()
spaces_key = os.getenv('DO_SPACES_KEY')
spaces_secret = os.getenv('DO_SPACES_SECRET')
spaces_region = os.getenv('DO_SPACES_REGION')
spaces_name = os.getenv('DO_SPACES_NAME')
endpoint_url = os.getenv('DO_SPACES_ENDPOINT')

class DigitalOceanClient:
    def __init__(self):
        self.client = Client(token=os.getenv("DIGITALOCEAN_TOKEN"))
        session = boto3.session.Session()
        self.client = session.client('s3',
                        region_name=spaces_region,
                        endpoint_url=endpoint_url,
                        aws_access_key_id=spaces_key,
                        aws_secret_access_key=spaces_secret)


    def upload_file(self,file_name,bucket='images', object_name=None, is_public=True):
        """Upload a file to an S3 bucket
        :param file_name: File to upload
        :param bucket: Bucket to upload to
        :param object_name: S3 object name. If not specified then file_name is used
        :return: True if file was uploaded, else False
        """
        if object_name is None:
            now = datetime.now()
            object_name_with_dt = file_name.split(".")[-2]+now.strftime("%Y%m%d%H%M%S") + "." + file_name.split(".")[-1]
        # Upload the file
        try:
            if is_public:
                self.client.upload_file(file_name, bucket, object_name_with_dt, ExtraArgs={'ACL':'public-read'})
            else:
                self.client.upload_file(file_name, bucket, object_name_with_dt)
            url = requote_uri(f"{endpoint_url}/{bucket}/{object_name_with_dt}")
            return url
        except Exception as e:
            print(f"Error uploading file: {e}")