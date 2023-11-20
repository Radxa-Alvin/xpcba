#!/usr/bin/python3
import add_path
add_path.apply()

from minio import Minio
from minio.error import S3Error

bucket = 'b-1251133331'


def get_client():
    client = Minio(
        'cos.ap-guangzhou.myqcloud.com',
        access_key='AKID4LANgllnJywlAdqYUra14ivkQzhLpgcH',
        secret_key='beRepOWyeDVxSAUjnliQUYGjvZ1II4w1',
        secure=False,
        region='ap-guangzhou',
    )
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)

    return client


def fput_object(object_name, file_path):
    client = get_client()
    try:
        client.fput_object(
            bucket, object_name, file_path,
        )
    except S3Error as exc:
        print('error occurred.', exc)
