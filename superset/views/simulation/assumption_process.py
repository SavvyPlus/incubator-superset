from .helper import *
from .util import *
from .simulation_config import start_date_str, end_date_str, sim_start_date_str, sim_end_date_str, \
    states, bucket_inputs, rooftop_pv_path, existing_generation_path, existing_generation_s3_pickle_path, \
    pv_data_s3_pickle_path, pv_forecast_s3_new_pickle_path, pv_history_s3_new_pickle_path, new_projects_pickle_path, \
    retirement_s3_pickle_path, demand_growth_rate_s3_pickle_path, renewable_proportion_s3_pickle_path, excel_path, bucket_test, \
    projects_gen_data_s3_pickle_path, small_battery_capacity_s3_pickle_path, sheet_demand_adjustment
import time
import datetime
import pandas as pd


# assumptions from excel file
def process_pv_forecast_history_assumption(filename, state, sim_start, sim_end, ref_start, ref_end):
    pv_forecast_df, pv_history_df = pv_assumption(filename)
    pv_forecast_dic = pv_get_forecast_dic(sim_start, sim_end, pv_forecast_df, pv_history_df, state)
    pv_history_dic = pv_get_history_dic(ref_start, ref_end, pv_history_df, state)
    pv_history_dic_new = dict()
    pv_forecast_dic_new = dict()
    for i in range((ref_end - ref_start).days + 1):
        test_day = ref_start + datetime.timedelta(days=i)
        pv_history_dic_new[test_day] = pv_history_dic[datetime.date(test_day.year, test_day.month, 1)]
    for i in range((sim_end-sim_start).days+1):
        test_sim_day = sim_start + datetime.timedelta(days=i)
        tmp = get_pv_forecast_delta(pv_forecast_dic, test_sim_day)
        pv_forecast_dic_new[test_sim_day] = tmp
    return pv_history_dic_new, pv_forecast_dic_new


def update_renewable_proportion_pickle(file_path, state, version):
    renewable_proportion_dict = max_renewable_proportion(file_path, state)
    write_pickle_to_s3(renewable_proportion_dict, bucket_inputs,
                       renewable_proportion_s3_pickle_path.format(version, state))


# data from S3 buckets
def process_pv_data(state, ref_start, ref_end):
    pv_df = read_from_s3(bucket_inputs, rooftop_pv_path.format(state))
    pv_dic = dict()
    for i in range((ref_end-ref_start).days+1):
        test_day = ref_start + datetime.timedelta(days=i)
        pv_data_current_day = \
            pv_df.query('year == {} & month == {} & day == {}'.format(test_day.year, test_day.month, test_day.day))
        pv_dic[test_day] = list(pv_data_current_day['POWER'])
    return pv_dic


def update_pv_data_and_assumption_pickle(file_path, assumptions_version):
    pv_data = dict()
    pv_history = dict()
    pv_forecast = dict()
    for current_state in states:
        start_time = time.time()
        print(current_state)
        ref_start_date = datestr2date(start_date_str)
        ref_end_date = datestr2date(end_date_str)
        sim_start_date = datestr2date(sim_start_date_str)
        sim_end_date = datestr2date(sim_end_date_str)

        pv_assumption_data = process_pv_forecast_history_assumption(file_path,
                                                                    current_state,
                                                                    sim_start_date, sim_end_date,
                                                                    ref_start_date, ref_end_date)
        pv_history[current_state] = pv_assumption_data[0]
        pv_forecast[current_state] = pv_assumption_data[1]
        pv_data_state = process_pv_data(current_state, ref_start_date, ref_end_date)
        pv_data[current_state] = pv_data_state
        # print(time.time() - start_time)
    write_pickle_to_s3(pv_data, bucket_inputs, pv_data_s3_pickle_path.format(assumptions_version))
    write_pickle_to_s3(pv_history, bucket_inputs, pv_history_s3_new_pickle_path.format(assumptions_version))
    write_pickle_to_s3(pv_forecast, bucket_inputs, pv_forecast_s3_new_pickle_path.format(assumptions_version))

def update_new_projects_pickle(filename, assumptions_version):
    project = read_excel(filename, sheet_name='NewFormat')
    project_list = project.to_dict('record')
    for project_dic in project_list:
        project_dic['StartDate'] = project_dic['StartDate'].date()
        project_dic['EndDate'] = project_dic['EndDate'].date()
    write_pickle_to_s3(project_list, bucket_inputs, new_projects_pickle_path.format(assumptions_version))

def update_retirement_pickle(filename, assumptions_version):
    retirement = read_excel(filename, sheet_name='Retirement', usecols='A:G', nrows=279)
    retirement_list = retirement.to_dict('record')
    for retirement_dic in retirement_list:
        retirement_dic['Closure Date'] = retirement_dic['Closure Date'].date()
        retirement_dic['Back To Service Date'] = retirement_dic['Back To Service Date'].date()
    write_pickle_to_s3(retirement_list, bucket_inputs, retirement_s3_pickle_path.format(assumptions_version))

def update_demand_growth_pickle(filename, assumptions_version):
    growth_rate = read_excel(filename, sheet_name='Demand_Growth', usecols='A:D', nrows=155)
    # print(growth_rate)
    growth_rate = growth_rate.to_dict('record')

    growth_rate_dic = {}
    for state in states:
        growth_rate_dic[state] = {}

    for row in growth_rate:
        growth_rate_dic[row['State']][row['Year']] = row['Growth']

    write_pickle_to_s3(growth_rate_dic, bucket_inputs, demand_growth_rate_s3_pickle_path.format(assumptions_version))

def update_renewable_prop(filename, assumptions_version):
    renewable_prop = read_excel(filename, sheet_name='Renewable_Proportion')
    renewable_prop = renewable_prop.to_dict('record')
    renewable_prop_dic = {}
    for state in states:
        renewable_prop_dic[state] = {}
    for row in renewable_prop:
        renewable_prop_dic[row['State']][row['Date'].date()] = row['Maximum Half-Hour Intermittent Proportion']
    write_pickle_to_s3(renewable_prop_dic,
                       bucket_inputs,
                       renewable_proportion_s3_pickle_path.format(assumptions_version))


def prepare_proxy(filename, assumptions_version):
    # start_time = time.time()
    ref_start_date = datestr2date(start_date_str)
    ref_end_date = datestr2date(end_date_str)
    project_assumption = projects_wind_solar_assumption(filename)
    proxy_info = proxy_assumption(filename)
    # TODO dont upload data, only check
    process_wind_solar_data(project_assumption, proxy_info, ref_start_date, ref_end_date, assumptions_version)


def update_small_battery(filename, assumptions_version):
    battery_capacity = read_excel(filename, sheet_name='Behind_The_Meter_Battery')
    battery_capacity = battery_capacity.to_dict('record')
    battery_capacity_dic = {}
    for state in states:
        battery_capacity_dic[state] = {}
    for row in battery_capacity:
        battery_capacity_dic[row['State']][row['Year']] = row['AGGREGATE_MW']
    write_pickle_to_s3(battery_capacity_dic,
                       bucket_inputs,
                       small_battery_capacity_s3_pickle_path.format(assumptions_version))


def update_strategic_behaviour(filename, assumptions_version):
    strategic_behaviour_dict = dict()
    for state in states:
        strategic_behaviour_dict[state] = get_strategic_behaviour_assumption(filename, state)
    write_pickle_to_s3(strategic_behaviour_dict, bucket_inputs,
                       strategic_behaviour_s3_pickle_path.format(assumptions_version))


def adjust_demand(filename):
    adjustment = pd.read_excel(filename, sheet_name=sheet_demand_adjustment)
    affected_dates_lst = [day.date() for day in set(adjustment.to_dict(orient='list')['Date'])]
    for day in affected_dates_lst:
        original_demand = read_pickle_from_s3(bucket_inputs, actual_total_demand_5_mins_path.format(day))
        curr_day_adj = \
            adjustment[adjustment['Date'] == datetime.datetime(day.year, day.month, day.day, 0, 0)].to_dict('record')
        for adj in curr_day_adj:
            fm = adj['SETTLEMENTDATE']
            region = adj['REGIONID']
            adjusted = adj['TOTALDEMAND_ADJUSTED']
            original_demand[fm][region] = adjusted
        write_pickle_to_s3(original_demand, bucket_inputs, adjusted_total_demand_5_mins_path.format(day))
        print(day)


def update_gas_price_escalation(filename, assumptions_version):
    for state in states:
        escalation_dict = get_gas_price_escalation_assumption(filename, state)
        write_pickle_to_s3(escalation_dict,
                           bucket_inputs,
                           gas_price_escalation_s3_pickle_path.format(assumptions_version, state))


def process_assumptions(file_path, assumptions_version):
    update_pv_data_and_assumption_pickle(file_path, assumptions_version)
    update_new_projects_pickle(file_path, assumptions_version)
    update_retirement_pickle(file_path, assumptions_version)
    update_demand_growth_pickle(file_path, assumptions_version)
    update_renewable_prop(file_path, assumptions_version)
    prepare_proxy(file_path, assumptions_version)
    update_small_battery(file_path, assumptions_version)
    update_strategic_behaviour(file_path, assumptions_version)
    adjust_demand(file_path)
    update_gas_price_escalation(file_path, assumptions_version)

def check_assumption(file_path, assumtpions_version):
    import xlrd
    xls = xlrd.open_workbook(file_path, on_demand=True)
    print(xls.sheet_names())
    for sheet in sheet_name_list:
        pass
    return 'success'

def check_proxy(file_path):
    return True



def upload_assumption_file(file_path, assumptions_version):
    put_file_to_s3(file_path, bucket_test, excel_path.format(assumptions_version))
    return get_download_url(bucket_test, excel_path.format(assumptions_version)), \
           get_s3_url(bucket_test, excel_path.format(assumptions_version))
