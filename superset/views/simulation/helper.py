from .util import read_excel, read_from_s3, write_pickle_to_s3
import pandas as pd
# from spot_price_simulation_lp.s3_utils import write_pickle_to_s3
import datetime
import calendar
from .simulation_config import *


def read_file_sheet(filename, sheet_name):
    """
        read assumption excel file
        :param filename: the file path
        :param sheet_name: the sheet name of target assumption
        :return:
        """
    df = read_excel(filename, sheet_name=sheet_name)
    return df


def get_one_day_data(date, df):
    new_data = df.query('year == {} & month == {} & day == {}'.format(date.year, date.month, date.day))
    new_data = new_data.drop(columns=['year', 'month', 'day'])
    return new_data


def get_df_map(df, ref_start_date, ref_end_date):
    df_dic = {}
    current_date = ref_start_date
    for i in range((ref_end_date - ref_start_date).days + 1):
        df_dic[current_date] = get_one_day_data(current_date, df)
        current_date += datetime.timedelta(days=1)
    return df_dic


def rename_header_with_top_row(df):
    """
        Rename the header of the DataFrame as the first row of the table
        :param df: the target DataFrame
        :return: new DataFrame
        """
    headers = df.iloc[0]
    return pd.DataFrame(df.values[1:], columns=headers)


def pv_assumption(filename):
    """
        Read the pv forecast and solar data as the DataFrame
        :param filename:
        :return:  pv solar DataFrame and pv forecast DataFrame
        """
    pv_forecast_df = read_file_sheet(filename, sheet_pv_forecast)
    pv_history_df = read_file_sheet(filename, sheet_pv_history)
    # pv_forecast_df = rename_header_with_top_row(pv_forecast_df)
    # pv_history_df = rename_header_with_top_row(pv_history_df)
    return pv_forecast_df, pv_history_df


def pv_get_forecast_dic(sim_start_date, sim_end_date, pv_forecast_df, pv_history_df, state):
    """
        convert pv forecast DataFrame to a dictionary
        :param sim_start_date: simulation state date
        :param sim_end_date: simulation end date
        :param pv_forecast_df: the pv forecast DataFrame
        :param pv_history_df: pv history DataFrame
        :param state: the target state
        :return: the dictionary of forecast data
                {
                    simulation year:{
                        'base': the base of the forecast of the year
                        'rate': the increase rate of the forecast
                        }
                }
        """
    pv_forecast_dic = dict()
    pv_forecast_temp_dic = dict()
    pv_forecast_df = pv_forecast_df.query(f"State == '{state}'")
    pv_forecast_df['Year'] = pv_forecast_df.Year.astype(int)
    pv_forecast_df['AGGREGATE_MW'] = pv_forecast_df.AGGREGATE_MW.astype(float)
    # year_start = pv_forecast_df['Year'].iloc[0]
    year_start = sim_start_date.year
    year_start_dt = datetime.datetime(sim_start_date.year, sim_start_date.month, sim_start_date.day)
    year_start_ts = pd.Timestamp(year=sim_start_date.year, month=sim_start_date.month, day=sim_start_date.day, hour=0)
    pv_start_capacity = \
        pv_history_df[pv_history_df.State == state][pv_history_df.Date == year_start_ts]['AGGREGATE_MW'].iloc[0]
    for i in range(year_start, sim_end_date.year + 1):
        pv_forecast = pv_forecast_df.query(f"Year == {i}")['AGGREGATE_MW'].iloc[0]
        pv_forecast_temp_dic[i] = pv_forecast

    for i in range(sim_start_date.year, sim_end_date.year + 1):
        if i == year_start:
            pv_forecast_dic[i] = {'base': pv_start_capacity,
                                  'rate': (pv_forecast_temp_dic[i] - pv_start_capacity) / (
                                      366 if calendar.isleap(i) else 365)}
        else:
            pv_forecast_dic[i] = {'base': pv_forecast_temp_dic[i - 1],
                                  'rate': (pv_forecast_temp_dic[i] - pv_forecast_temp_dic[i - 1]) / (
                                      366 if calendar.isleap(i) else 365)}
    return pv_forecast_dic


def pv_get_history_dic(ref_start_date, ref_end_date, pv_history_df, state):
    """
        get the solar dictionary of the target state within the historical data date range
        :param ref_start_date: the start of historical data
        :param ref_end_date: the end of historical data
        :param pv_history_df: pv solar DataFrame
        :param state: the state
        :return: dictionary of pv history data
                {
                    ref_date: pv_solar value
                }
        """
    pv_history_dic = dict()
    current_date = ref_start_date
    # how many months between the reference start and end
    length = (ref_end_date.year - ref_start_date.year - 1) * 12 + (13 - ref_start_date.month) + ref_end_date.month
    pv_history_df = pv_history_df.query(f"State == '{state}'")
    for i in range(length):
        pv_history = pv_history_df.loc[pv_history_df['Date'] ==
                                       datetime.datetime(current_date.year, current_date.month, 1)]['AGGREGATE_MW'].iloc[0]
        pv_history_dic[current_date] = pv_history
        current_date = datetime.date(year=current_date.year, month=current_date.month + 1,
                                     day=current_date.day) \
            if current_date.month < 12 else datetime.date(year=current_date.year + 1, month=1, day=current_date.day)
    return pv_history_dic


def get_pv_forecast_delta(pv_forecast_dic_t, the_sim_date):
    """
    :param pv_forecast_dic_t:
    :param the_sim_date: datetime.date
    :return:
    """
    current_year_start_date = datetime.date(the_sim_date.year, 1, 1)
    delta = the_sim_date - current_year_start_date
    return pv_forecast_dic_t[the_sim_date.year]['base'] + pv_forecast_dic_t[the_sim_date.year][
        'rate'] * delta.days


def max_renewable_proportion(file_path, state):
    """
        read renewable proportion assumption data and convert it to a dictionary
        :param file_path: the assumption file
        :param state: the target state
        :return: the renewable proportion dictionary
                {
                    date : value
                }
        """
    max_renewable_proportion_df = read_file_sheet(file_path, sheet_renewable_proportion)
    # max_renewable_proportion_df = rename_header_with_top_row(max_renewable_proportion_df)
    max_renewable_proportion_df = max_renewable_proportion_df.query(f"State == '{state}'")
    max_renewable_proportion_dict = dict()
    for index, row in max_renewable_proportion_df.iterrows():
        max_renewable_proportion_dict[row['Date'].date()] = row['Maximum Half-Hour Intermittent Proportion']
    return max_renewable_proportion_dict


def floor_price_assumption(file_path, state):
    """
        the floor price of the target state
        :param file_path: the assumption file
        :param state: the target state
        :return: the dictionary of floor price
                {
                    date:value
                }
        """
    floor_price_df = read_file_sheet(file_path, sheet_floor_price)
    # floor_price_df = rename_header_with_top_row(floor_price_df)
    floor_price_df = floor_price_df.query(f"State == '{state}'")
    floor_price_dic_t = dict()
    for index, row in floor_price_df.iterrows():
        floor_price_dic_t[row['Date'].date()] = row['Floor Price ($/MWh)']
    return floor_price_dic_t


def projects_wind_solar_assumption(file_path):
    """
        read project list from assumption file
        :param file_path: the assumption file path
        :return: dictionaries of projects and its proxy_projects
    """
    project_df = read_file_sheet(file_path, sheet_project_list)
    # project_df = rename_header_with_top_row(project_df)
    projects_ref_dic = {}
    for index, row in project_df.iterrows():
        if row['Quantity'] != 0 and (row['FuelType'] in ['Solar', 'Wind']):
            projects_ref_dic[row['DUID']] = {'type': row['FuelType'],
                                             'capacity': row['Quantity'],
                                             'date': row['StartDate'],
                                             'proxy': row['Proxy']}
    return projects_ref_dic


def proxy_assumption(file_path):
    proxy_df = read_file_sheet(file_path, sheet_project_proxy)
    # proxy_df = rename_header_with_top_row(proxy_df)
    proxy_capacity_dic = {}
    for index, row in proxy_df.iterrows():
        proxy_capacity_dic[row['Project']] = {'capacity': row['Nameplate Capacity (MW)'],
                                              'type': row['Technology Type'],
                                              'state': row['State']}
    return proxy_capacity_dic


def process_wind_solar_data(project_ref_dic, proxy_capacity_dic, ref_start_date, ref_end_date, assumptions_version):
    # make a set for project proxies
    proxy_set = set()
    for key in project_ref_dic:
        proxy_set.add(project_ref_dic[key]['proxy'])
    # make a dictionary of project proxies and their historical generation data
    proxy_data_dic = {}  # {project_proxy: {ref_date: data}}
    for project in proxy_set:
        print(project)
        gen_data_df = read_from_s3(bucket_inputs, wind_solar_path.format(proxy_capacity_dic[project]['state'],
                                                                         proxy_capacity_dic[project]['type'].lower(),
                                                                         project))
        proxy_dic = get_df_map(gen_data_df, ref_start_date, ref_end_date)
        proxy_data_dic[project] = proxy_dic

    # historical_generation = dict()
    for i in range((ref_end_date - ref_start_date).days + 1):
        test_day = ref_start_date + datetime.timedelta(days=i)
        test_day_str = test_day.strftime("%Y-%m-%d")
        historical_generation_one_day = dict()
        for key in project_ref_dic:
            ratio = project_ref_dic[key]['capacity'] / proxy_capacity_dic[project_ref_dic[key]['proxy']]['capacity']
            # a list of 48 half hour generation data
            historical_generation_one_day[key] = \
                list(proxy_data_dic[project_ref_dic[key]['proxy']][test_day].iloc[:, 0] * ratio)
        write_pickle_to_s3(historical_generation_one_day,
                           bucket_inputs,
                           projects_gen_data_s3_pickle_path.format(assumptions_version, test_day_str))


def get_strategic_behaviour_assumption(file_path, state):
    """
    Read the strategic behaviour assumptions spreadsheet to get the numbers that the model needs
    :return: dictionary of total demand bins, probabilities and strategic impacts to demand
    :rtype: dict like {
                        'starting': bin start,
                        'ending': bin end,
                        'step': bin step
                        'data':{
                            probability : MW
                        }
                      }
    """
    strategic_behaviour_df = read_file_sheet(file_path, sheet_strategic_behaviour)
    # strategic_behaviour_df = rename_header_with_top_row(strategic_behaviour_df)
    strategic_behaviour_df = strategic_behaviour_df.query(f"State == '{state}'")
    strategic_behaviour_df = strategic_behaviour_df.drop(columns=['State'])

    strategic_behaviour_df = strategic_behaviour_df.set_index('Bin (not Exceeding)')
    # For each row, get the cumulative probabilities by columns
    # convert to dictionary
    strategic_behaviour_cumsum_dict = strategic_behaviour_df.to_dict(orient='split')
    # get the first, last numbers in the bins, and the step
    strategic_behaviour_dict = dict()
    strategic_behaviour_dict['starting'] = strategic_behaviour_cumsum_dict['index'][0]
    strategic_behaviour_dict['step'] = \
        strategic_behaviour_cumsum_dict['index'][1] - strategic_behaviour_cumsum_dict['index'][0]
    strategic_behaviour_dict['ending'] = strategic_behaviour_cumsum_dict['index'][-1]
    strategic_data_dic = dict()
    for i in range(strategic_behaviour_dict['starting'], strategic_behaviour_dict['ending'] + 1,
                   strategic_behaviour_dict['step']):
        temp_df = strategic_behaviour_df.query(f" index == {i}")
        percentage = 0
        i_dict = dict()
        for row in temp_df.values:
            percentage += row[0]
            i_dict[percentage] = row[1]
        strategic_data_dic[i] = i_dict
    strategic_behaviour_dict['data'] = strategic_data_dic

    return strategic_behaviour_dict


def get_generation_closure_assumption(file_path, state):
    """
    Read the generation closure assumptions from the spreadsheet
    :return: retirements information including power station name, adjustment factor, closure date
    :rtype: dict like {'power station': {'Adjustment Factor': , 'Closure Date': }, ...}
    """
    generation_closure_df = read_file_sheet(file_path, sheet_generation_closure)
    # generation_closure_df = rename_header_with_top_row(generation_closure_df)
    generation_closure_df = generation_closure_df.query(f"`Impact To State`=='{state}'")
    generation_closure_df = generation_closure_df.set_index('DUID')
    generation_closure_dict = generation_closure_df.to_dict(orient='index')
    return generation_closure_dict


def get_generation_closure_data(retirements, ref_start_date, ref_end_date):
    """
    load the data from S3 into dictionary
    :param retirements: the dict from generation closures assumptions
    :param ref_start_date: ref start date
    :param ref_end_date: ref end date
    :return: the generation closures data
    :rtype: dict
    """
    generation_closures = dict()
    for duid in retirements.keys():
        closure = read_from_s3(bucket_inputs, gen_closure_path.format(retirements[duid]['State'], 'retirement', duid))
        generation_closures[duid] = {
            'data': get_df_map(closure, ref_start_date, ref_end_date),
            'Adjustment Factor': retirements[duid]['Adjustment Factor'],
            'Closure Date': retirements[duid]['Closure Date'],
            'Back To Service Date': retirements[duid]['Back To Service Date']
        }
    return generation_closures


def get_new_power_stations_assumption(file_path, state):
    """
    make a dictionary like the following structure from the new power stations information of current state.
    :param file_path:
    :param state:
    :return: dictionary{
                            ID: {
                                'name': new power station name,
                                'fuel type': its fuel type,
                                'start': start date,
                                'end': end date,
                                'adjustment': [
                                                {'lower': xxx, 'upper': xxx, 'qty': xxx},
                                                {},
                                                ...
                                                ]
                            },
                            ...
                        }
    """
    new_ps_dict = dict()
    new_ps_df = read_file_sheet(file_path, sheet_new_power_stations)
    # new_ps_df = rename_header_with_top_row(new_ps_df)
    new_ps_df = new_ps_df.query(f"`Region`=='{state}'")
    stations_id = new_ps_df[new_ps_df.columns[0]].unique().tolist()
    for nps_id in stations_id:
        tmp_df = new_ps_df.query(f"`ID`=={nps_id}")
        price_adjustment_tmp = []
        for i in range(len(tmp_df)):
            price_adjustment_tmp.append({'lower': tmp_df['PriceThresholdLower'].iloc[i],
                                         'upper': tmp_df['PriceThresholdUpper'].iloc[i],
                                         'qty': tmp_df['Quantity'].iloc[i]
                                         })
        new_ps_tmp_dict = {'name': tmp_df['Name'].iloc[0],
                           'fuel type': tmp_df['FuelType'].iloc[0],
                           'start': tmp_df['StartDate'].iloc[0],
                           'end': tmp_df['EndDate'].iloc[0],
                           'adjustment': price_adjustment_tmp}
        new_ps_dict[nps_id] = new_ps_tmp_dict
    return new_ps_dict


def get_gas_price_escalation_assumption(file_path, state):
    """
    make a dictionary like the following structure from the gas price escalation information of current state.
    :param file_path:
    :param state:
    :return: dictionary{year: [case1, case2, ..., case9],
                        ...,
                        }
    """
    escalation_dict = dict()
    escalation_df = read_file_sheet(file_path, sheet_escalation)
    # escalation_df = rename_header_with_top_row(escalation_df)
    escalation_df = escalation_df.query(f"`State`=='{state}'")
    year_list = escalation_df['Year'].tolist()
    for year in range(len(year_list)):
        escalation_factor = escalation_df.iloc[year, 2:].tolist()
        escalation_dict[year_list[year]] = escalation_factor
    return escalation_dict

