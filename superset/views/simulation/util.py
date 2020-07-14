from datetime import datetime, date, timedelta
import time
import json
import s3fs
import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd
import numpy as np
import boto3
import pickle
import logging
from urllib import parse
from requests import get
from .simulation_config import states, nifi_sqs_url

logging.getLogger('botocore').setLevel(logging.CRITICAL)
logging.getLogger('boto3').setLevel(logging.CRITICAL)

fs = s3fs.S3FileSystem()
client = boto3.client('s3', region_name='ap-southeast-2')
sqs = boto3.client('sqs', region_name='ap-southeast-2')

def read_pickle_from_s3(bucket, path):
    pickle_data = client.get_object(Bucket=bucket, Key=path)
    return pickle.loads(pickle_data['Body'].read())

def write_pickle_to_s3(data, bucket, path):
    pickle_data = pickle.dumps(data)

    # TODO DEBUG do not write to s3
    client.put_object(Bucket=bucket, Body=pickle_data, Key=path)

def put_file_to_s3(filename, bucket, key, is_public=False):
    with open(filename, "rb") as f:
        if is_public:
            response = client.upload_fileobj(f, bucket, key, ExtraArgs={'ACL': 'public-read'})
        else:
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

def download_from_s3(bucket, key, path):
    client.download_file(bucket, key, path)

def read_from_s3(bucket, path):
    bucket_uri = f's3://{bucket}/{path}'
    dataset = pq.ParquetDataset(bucket_uri, filesystem=fs)
    table = dataset.read()
    df = table.to_pandas()
    return df

def send_sqs_msg(message_body, delay=10,
                 queue_url=nifi_sqs_url):

    response = sqs.send_message(
        QueueUrl=queue_url,
        DelaySeconds=delay,
        MessageBody=(message_body)
    )
    return response.get("MessageId", "")


def list_object_keys(bucket, prefix):
    key_list = []
    response = client.list_objects_v2(
        Bucket=bucket,
        Prefix=prefix
    )
    if response['KeyCount'] <= 0:
        return []
    contents = response['Contents']
    is_truncated = response['IsTruncated']

    for content in contents:
        key_list.append(content['Key'])

    if is_truncated:
        cont_token = response['NextContinuationToken']
    while is_truncated:
        response = client.list_objects_v2(
            Bucket=bucket,
            Prefix=prefix,
            ContinuationToken=cont_token
        )
        contents = response['Contents']
        is_truncated = response['IsTruncated']
        for content in contents:
            key_list.append(content['Key'])
        if is_truncated:
            cont_token = response['NextContinuationToken']

    return sorted(key_list)

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


# @df_state_error_checker
def read_excel(*args, **kwargs):
    df = pd.read_excel(*args, **kwargs)
    return df

def read_csv(*args, **kwargs):
    df = pd.read_csv(*args, **kwargs)
    return df


def get_redirect_endpoint(table_name: str, table_id: int) -> str:
    if 'distribution' in table_name:
        endpoint = "/superset/explore/?form_data={}".format(
            parse.quote_plus(json.dumps({
                "queryFields": {},
                "datasource": str(table_id) + "__table",
                "viz_type": "spot_price_histogram",
                "url_params": {},
                "time_range_endpoints": ["inclusive", "exclusive"],
                "granularity_sqla": None,
                "time_range": "Last week",
                "spot_hist_chart_type_picker": "value",
                "state_static_picker": "NSW1",
                "period_type_static_picker": "CalYear",
                "period_finyear_picker": None,
                "period_calyear_picker": None,
                "period_quarterly_picker": None},
                separators=(',', ':')))
        )
    else:
        endpoint = "/superset/explore/?form_data={}".format(
            parse.quote_plus(json.dumps({
                "queryFields": {"metrics": "metrics", "groupby": "groupby"},
                "datasource": str(table_id) + "__table",
                "viz_type": "multi_boxplot",
                "url_params": {},
                "time_range_endpoints": ["inclusive", "exclusive"],
                "granularity_sqla": None,
                "time_range": "Last week", "metrics": ["count"],
                "adhoc_filters": [], "groupby": [],
                "whisker_options": "Min/max (no outliers)",
                "period_type_static_picker": "CalYear", "period_finyear_picker": None,
                "period_calyear_picker": None, "period_quarterly_picker": None},
                separators=(',', ':')))
        )

    return endpoint


def get_current_external_ip():
    # return 'http://{}:8088'.format(get('https://api.ipify.org').text)
    # return 'http://{}:8088'.format('10.61.146.25')
    return 'https://app.empoweranalytics.com.au'

def get_full_week_end_date(start_date, end_date):
    total_days = (end_date - start_date).days+1
    end_date = end_date - timedelta(days=total_days % 7)
    return end_date
