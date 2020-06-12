from datetime import datetime, date
import time
import s3fs
import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd
import numpy as np
import boto3
import pickle
import logging
from requests import get
from .simulation_config import states, sqs_url

logging.getLogger('botocore').setLevel(logging.CRITICAL)
logging.getLogger('boto3').setLevel(logging.CRITICAL)

fs = s3fs.S3FileSystem()
client = boto3.client('s3')
sqs = boto3.client('sqs', region_name='ap-southeast-2')

def read_pickle_from_s3(bucket, path):
    pickle_data = client.get_object(Bucket=bucket, Key=path)
    return pickle.loads(pickle_data['Body'].read())

def write_pickle_to_s3(data, bucket, path):
    pickle_data = pickle.dumps(data)

    # TODO DEBUG do not write to s3
    bucket = "empower-simulation"
    client.put_object(Bucket=bucket, Body=pickle_data, Key=path)

def put_file_to_s3(filename, bucket, key):
    bucket = "empower-simulation"
    with open(filename, "rb") as f:
        response = client.upload_fileobj(f, bucket, key)
    return response

def get_download_url(bucket, key):
    return "https://{}.s3-ap-southeast-2.amazonaws.com/{}".format(bucket, key)

def get_s3_url(bucket, key):
    return "s3://{}/{}".format(bucket, key)


def put_object_to_s3(binary_data, bucket, key):
    client.put_object(Body=binary_data,
                      Bucket=bucket,
                      Key=key)

def read_from_s3(bucket, path):
    bucket_uri = f's3://{bucket}/{path}'
    dataset = pq.ParquetDataset(bucket_uri, filesystem=fs)
    table = dataset.read()
    df = table.to_pandas()
    return df

def send_sqs_msg(message_body, delay=10,
                        queue_url=sqs_url):

    response = sqs.send_message(
        QueueUrl=queue_url,
        DelaySeconds=delay,
        MessageBody=(message_body)
    )
    return response.get("MessageId", "")

def write_to_s3(data, bucket, path):
    bucket_uri = f's3://{bucket}/{path}'
    data_df = pd.DataFrame(np.array(data))
    table = pa.Table.from_pandas(data_df, preserve_index=False)
    pq.write_to_dataset(table, root_path=bucket_uri, filesystem=fs)


def write_to_s3_pandas_with_partition(data_df, bucket, path, partition_columns):
    bucket_uri = f's3://{bucket}/{path}'
    table = pa.Table.from_pandas(df=data_df, preserve_index=False)
    pq.write_to_dataset(table, root_path=bucket_uri, filesystem=fs, partition_cols=partition_columns)


def write_to_s3_pandas_without_partition(data_df, bucket, path):
    bucket_uri = f's3://{bucket}/{path}'
    table = pa.Table.from_pandas(df=data_df, preserve_index=False)
    pq.write_to_dataset(table, root_path=bucket_uri, filesystem=fs)

def datestr2date(dstr):
    """
    Convert string to datetime
    :type dstr: string
    :return: datetime
    """
    return datetime.strptime(dstr, "%Y-%m-%d").date()


def str2date(dstr):
    """
    Convert string to datetime
    :type dstr: string
    :return: datetime
    """
    return datetime.strptime(dstr, "%Y-%m-%d %H:%M:%S").date()


def date2num(dtime):
    """
    Covert datetime to number
    :type dtime: datetime
    :rtype: int
    """
    return date.toordinal(dtime)


def str2HH(dstr):
    """
    Convert string to time array
    :type dstr: string
    :return: time array
    """
    return time.strptime(dstr, "%Y-%m-%d %H:%M:%S")


def timearray2timestamp(dtime):
    """
    Covert time array to timestamp
    :type dtime: datetime
    :rtype: int
    """
    return int(time.mktime(dtime))

def df_state_error_checker(f):
    def wrap(*args, **kwargs):
        result = f(*args, **kwargs)
        if "State" in result.columns:
            for index,row in result.iterrows():
                if row['State'] not in states:
                    raise Exception("State Error in sheet {}: {}".format(kwargs['sheet_name'], row['State']))
        return result
    return wrap


@df_state_error_checker
def read_excel(*args, **kwargs):
    df = pd.read_excel(*args, **kwargs)
    return df

def get_current_external_ip():
    return 'http://{}:8088'.format(get('https://api.ipify.org').text)
