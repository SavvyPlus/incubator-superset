import boto3
import json
import time
import threading
import datetime

from superset import celery_app, simulation_logger

from .util import write_pickle_to_s3, read_pickle_from_s3, list_object_keys
from .simulation_config import bucket_test, bucket_inputs

client = boto3.client('lambda', region_name='ap-southeast-2')
s3 = boto3.client('s3', region_name='ap-southeast-2')



def invoker(payload, function_name='spot-simulation-prod-stk2-lp-v2'):
    response = client.invoke(
        FunctionName=function_name,
        InvocationType='Event',
        LogType='Tail',
        Payload=json.dumps(payload),
    )
    # print(payload['sim_tag'], payload['sim_index'], payload['sim_ref_dates'])


def batch_invoke(sim_tag, sim_ref_para, sim_index):
    threads = []

    for sim_ref_dates in sim_ref_para[sim_index]:
        sim_ref_dates = [([sr['sim_date'].year, sr['sim_date'].month, sr['sim_date'].day],
                          [sr['ref_date'].year, sr['ref_date'].month, sr['ref_date'].day]) for sr in sim_ref_dates]

        payload = {"sim_tag": sim_tag,
                   "sim_index": sim_index,
                   "sim_ref_dates": sim_ref_dates}
        t = threading.Thread(target=invoker, args=(payload,))
        threads.append(t)
        t.start()
        # break  # uncomment it if only want to run one call for test


def merger(sim_index, sim_tag):
    payload = {"sim_index": sim_index, "sim_tag": sim_tag}
    response = client.invoke(
        FunctionName='spot-simulation-prod-stk2-merger',
        InvocationType='Event',
        Payload=json.dumps(payload),
    )


def merger2(sim_index, sim_tag, prefix, output_name, bucket_from=bucket_inputs, bucket_to=bucket_test):
    payload = {"sim_index": sim_index,
               "sim_tag": sim_tag,
               "prefix": prefix,
               "output_name": output_name,
               "bucket_from": bucket_from,
               "bucket_to": bucket_to}
    response = client.invoke(
        FunctionName='spot-simulation-prod-stk2-merger',
        InvocationType='Event',
        Payload=json.dumps(payload),
    )


def vary_waiting_time(orig_time):
    new_time = orig_time - max((orig_time-50)//3, 3)
    return max(new_time, 40)


def invoker_back(payload, function_name='spot-price-lp-v2-backcast'):
    response = client.invoke(
        FunctionName=function_name,
        InvocationType='Event',
        LogType='Tail',
        Payload=json.dumps(payload),
    )
    print(payload['sim_tag'], payload['sim_index'], payload['sim_date'], payload['ref_date'])


def backcasting(sim_tag, sim_index, start_date, end_date):
    threads = []
    date_range = [start_date+datetime.timedelta(days=day) for day in range((end_date-start_date).days)]
    for date in date_range:
        payload = {"sim_tag": sim_tag,
                   "sim_index": sim_index,
                   "sim_date": [date.year, date.month, date.day],
                   "ref_date": [date.year, date.month, date.day]}
        t = threading.Thread(target=invoker_back, args=(payload, 'spot-price-lp-v2-backcast'))
        threads.append(t)
        t.start()
        # break  # uncomment it if only want to run one call for test


def batch_invoke_solver(bucket_inputs, sim_tag, start_index, end_index, interval=60):
    sim_ref_para = read_pickle_from_s3(bucket_inputs, f'cache/{sim_tag}/parameters_for_batch_test2.pickle')
    for sim_index in range(start_index, end_index):
        batch_invoke(sim_tag, sim_ref_para, sim_index)
        time.sleep(interval)


def batch_invoke_merger_year(bucket_outputs, sim_tag, start_index, end_index, output_count, year_start=2020, year_end=2031, interval=60):
    for sim_index in range(start_index, end_index):
        print(sim_index)
        res_list = list_object_keys(bucket_outputs, f'simulation-result/{sim_tag}/{sim_index}/')
        if len(res_list) < output_count:
            # Originally check equal, for this check if less
            print(f"{len(res_list)} records found, expect {output_count}")
            break
        for year in range(year_start,year_end):
            merger2(sim_index, sim_tag, str(year), f"SUMMARY-{year}.pickle", bucket_outputs, bucket_outputs)
        print(f"{len(res_list)} record found, check passed, continue next batch soon")
        time.sleep(interval)


def batch_invoke_merger_all(bucket_inputs, sim_tag, start_index, end_index, output_count, interval=60):
    for sim_index in range(start_index, end_index):
        print(sim_index)
        res_list = list_object_keys(bucket_inputs, f'result-spot-price-simulation-lp/{sim_tag}/{sim_index}/SUMMARY-')
        if len(res_list) < output_count:
            # Originally check equal, for this check if less
            print(f"{len(res_list)} records found, expect {output_count}")
            break
        merger2(sim_index, sim_tag, 'SUMMARY-', 'SUMMARY.pickle', bucket_inputs, bucket_inputs)
        print(f"{len(res_list)} record found, check passed, continue next batch soon")
        time.sleep(interval)

# @celery_app.task
# @simulation_logger.log_simulation(action_name='invoke')
# def simulation_start_invoker(run_id, start_date, end_date, sim_name, sim_num):
#     from flask import g
#     # bucket_inputs = '007-spot-price-forecast-physical'
#     # bucket_outputs = "dex-empower.test"
#     from .batch_parameters import generate_parameters_for_batch
#     generate_parameters_for_batch(run_id, sim_num)
#     index_start = 0
#     index_end = sim_num  # exclusive
#
#     sim_tag = run_id
#     total_days = start_date - end_date
#     output_days = total_days + 7 - total_days%7
#     g.result = 'invoke success'
#     g.action_object = sim_name
#     g.action_object_type = 'simulation'
#     batch_invoke_solver(bucket_test, sim_tag, index_start, index_end, interval=60)
#     batch_invoke_merger_year(bucket_test, sim_tag, index_start, index_end, output_days, year_start=simulation.start_date.year,
#                              year_end=simulation.end_date.year, interval=30)
#     batch_invoke_merger_all(bucket_test, sim_tag, index_start, index_end, output_count=11, interval=60)
