# basic settings for simulation
weather_history_start = "2011-01-01"
# weather_history_end = "2019-12-31"
weather_history_end = "2019-07-31"
start_date_str = "2017-01-01"
# end_date_str = "2019-12-31"
end_date_str = "2019-07-31"
sim_start_date_str = "2020-01-01"
sim_end_date_str = "2040-12-25"
base_station_name = 'MELBOURNE AIRPORT'
base_state = 'VIC1'
# states = ['VIC1', 'NSW1', 'QLD1', 'SA1', 'TAS1']
states = sorted(['VIC1', 'NSW1', 'QLD1', 'SA1', 'TAS1'])
public_holidays_def = 'AFMA'
inter_connectors_main = ['T-V-MNSP1', 'V-SA', 'VIC1-NSW1', 'NSW1-QLD1']
inter_connectors_main_dic = {'T-V-MNSP1': "TAS1-VIC1",
                             'V-SA': "VIC1-SA1",
                             'VIC1-NSW1': "VIC1-NSW1",
                             'NSW1-QLD1': "NSW1-QLD1"}
ic_list = ["VIC1-NSW1", "VIC1-SA1", "TAS1-VIC1", "NSW1-QLD1"]
# CPT 17/18, 18/19, 19/20, 20/21, 21/22, 22/23, 23/24, 24/25
cpt = {'FY-17/18': 212800, 'FY-18/19': 216900, 'FY-19/20': 221100,
       'FY-20/21': 223500, 'FY-21/22': 226500, 'FY-22/23': 229500,
       'FY-23/24': 232500, 'FY-24/25': 235500, 'FY-25/26': 238500,
       'FY-26/27': 241500, 'FY-27/28': 244500, 'FY-28/29': 247500,
       'FY-29/30': 250500, 'FY-30/31': 253500, 'FY-31/32': 256500,
       'FY-32/33': 259500, 'FY-33/34': 262500, 'FY-34/35': 265500,
       'FY-35/36': 268500, 'FY-36/37': 271500, 'FY-37/38': 274500,
       'FY-38/39': 277500, 'FY-39/40': 280500, 'FY-40/41': 283500}

# months for each season type
summer = (1, 2, 3, 11, 12)
winter = (5, 6, 7, 8)
shoulder = (4, 9, 10)

# assumption file sheet name
sheet_pv_forecast = 'Rooftop_Solar_Forecast'
sheet_pv_history = 'Rooftop_Solar_History'
sheet_generation_closure = 'Retirement'
sheet_demand_growth = 'Demand_Growth'
sheet_project_list = 'NewFormat'
sheet_project_proxy = 'Project_Proxy'
# sheet_new_power_stations = "New_Power_Stations"
sheet_strategic_behaviour = "Strategic_Behaviour"
# sheet_floor_price = "LGC_Floor_Price"
sheet_renewable_proportion = "Renewable_Proportion"
sheet_demand_adjustment = 'Demand_Adjustments'
sheet_behind_the_meter_battery = 'Behind_The_Meter_Battery'
sheet_escalation = 'Gas_Price_Escalation'
sheet_retirement = 'Retirement'
sheet_mpc = 'MPC_CPT'
sheet_col_dict = {
    'Project_Proxy':['Project','Nameplate Capacity (MW)','Technology Type','State'],
    'Behind_The_Meter_Battery':['State','Year','AGGREGATE_MW'],
    'Demand_Growth':['State','Year','Growth'],
    'Gas_Price_Escalation':['State','Year'],
    'MPC_CPT':['MPC'],
    'NewFormat':['StartDate','EndDate','DUID','FuelType','InstalledQuantity','MaximumQuantity','Proxy'],
    'Rooftop_Solar_Forecast':['State','Year','AGGREGATE_MW'],
    'Rooftop_Solar_History':['State','Date','CAPACITY_MW','AGGREGATE_MW'],
    'Renewable_Proportion':['State','Date','Maximum Half-Hour Intermittent Proportion'],
    'Retirement':['Closure Date','Back To Service Date'],
    'Strategic_Behaviour':['State','Bin (not Exceeding)','value','MW']
}
sheet_col_name_to_tab_col_name_dict = {
    'Project_Proxy':{
        'Nameplate Capacity (MW)': 'Nameplate_Capacity_MW',
        'Technology Type': 'Technology_Type',
        'Tracking Type': 'Tracking_Type',
    },
    'NewFormat': {
        'StartDate': 'Start_Date',
        'EndDate': 'End_Date',
        'FuelType': 'Fuel_Type',
        'InstalledQuantity': 'Installed_Quantity',
        'MaximumQuantity': 'Maximum_Quantity',
        'ProbabilityOfSuccess': 'Probability_Of_Success',
        'Region': 'State',
        'OfferRate': 'Offer_Rate',
    },
    'Renewable_Proportion': {
        'Maximum Half-Hour Intermittent Proportion': 'Maximum_HalfHour_Intermittent_Proportion'
    },
    'Retirement': {
        'Registered Capacity': 'Registered_Capacity',
        'Impact To State': 'Impact_To_State',
        'Adjustment Factor': 'Adjustment_Factor',
        'Closure Date': 'Closure_Date',
        'Back To Service Date': 'Back_To_Service_Date',
    },
    'Strategic_Behaviour':{
        'Bin (not Exceeding)': 'Bin_Not_Exceeding',
    },
}


# MSSQL data source
# db_host = "AWS2-SVR-DB-002"
db_host = "10.61.129.150"
db_user = "spotforecast"
db_pass = "Kjd)3i848(*3920029jdjsks_23knN"
db_MarketData = "MarketData"
db_OperationalReporting = "OperationalReporting"
db_ElecMMS = "ElecMMS"
db_AEMO_ElecMMS = "AEMO_ElecMMS"
schema_weather = "dbo.BOM_Daily"
schema_GenSource = "NEM.GenerationSource"
schema_Gen = "NEM.GenerationByUnit_30min"
schema_PD = "NEM.PreDispatchPriceSensitivities"
schema_SP = "NEM.SpotPriceDemand_30min"
schema_PHols = "dbo.Public_Holidays"
schema_Interconnector = "[dbo].[DISPATCHINTERCONNECTORRES]"
schema_TradingRegionSum = "[dbo].[TRADINGREGIONSUM]"
schema_RooftopPV = "[dbo].[AEMO_ROOFTOP_PV_ACTUAL]"
schema_RooftopPV_new = "[dbo].[ROOFTOP_PV_ACTUAL]"

# MySQL data source
db_host_mysql = "aws2-savvyplus-mysql-elecmms.cluster-c1hb7du4frej.ap-southeast-2.rds.amazonaws.com"
db_username_mysql = "mysqluser"
db_pass_mysql = "Elecmms_2020"
db_schema_ElecMMS3 = "ElecMMS3"

# S3 data folders:
bucket_inputs = "007-spot-price-forecast-physical"
bucket_test = "empower-simulation"
rooftop_pv_path = 'historical-generation/{}/rooftop-pv'  # state
public_holiday_path = 'public_holiday/{}.pickle'  # state
wind_solar_path = 'historical-generation/{}/{}/{}'  # state, wind/solar, duid
existing_generation_path = 'historical-generation/{}/existing'  # state, existing
total_demand_path = 'total-demand/{}'  # state
gen_closure_path = 'historical-generation/{}/{}/{}'  # state, retirement, DUID
inter_connector_5_min_all_vars_path = 'inter-connectors-5-min-all-vars/{}'  # inter-connector id, year, month, day
inter_connector_5_min_path = 'inter-connectors-5-min/{}/year={}/month={}/day={}'  # inter-connector id, year, month, day
inter_connector_5_min_all_vars_pkl_path = 'inter-connectors-5-min-all-vars-pkl/{}/{}.pickle' # inter-connector id, date

adjusted_offerbands_path = 'nem-pricing-v2/adjusted_offerbands/{}.pickle'  # date
adjusted_offerbands_v7_5_mins_path = 'nem-pricing-v2/adjusted_offerbands_v7_5_mins/{}.pickle'  # date
adjusted_offerbands_v7a_5_mins_path = 'nem-pricing-v2/adjusted_offerbands_v7a_5_mins/{}.pickle'  # date
adjusted_offerbands_v7_5_mins_two_parts_path = 'nem-pricing-v2/adjusted_offerbands_v7_5_mins_two_parts/{}.pickle'  # date
adjusted_offerbands_v8_5_mins_path = 'nem-pricing-v2/adjusted_offerbands_v8_5_mins/{}.pickle'  # date
adjusted_offerbands_v9_5_mins_path = 'nem-pricing-v2/adjusted_offerbands_v9_5_mins/{}.pickle'  # date
adjusted_offerbands_v9a_5_mins_path = 'nem-pricing-v2/adjusted_offerbands_v9a_5_mins/{}.pickle'  # date, v8, use savvy demand
adjusted_offerbands_v9b_5_mins_path = 'nem-pricing-v2/adjusted_offerbands_v9b_5_mins/{}.pickle'  # date, v8, use total demand
adjusted_offerbands_v9c_5_mins_path = 'nem-pricing-v2/adjusted_offerbands_v9c_5_mins/{}.pickle'  # date, v8, use total demand

adjusted_offerbands_v10_5_mins_path = 'nem-pricing-v2/adjusted_offerbands_v10_5_mins/{}.pickle'  # date
adjusted_offerbands_v10b_5_mins_path = 'nem-pricing-v2/adjusted_offerbands_v10b_5_mins/{}.pickle'  # date
adjusted_offerbands_v10c_5_mins_path = 'nem-pricing-v2/adjusted_offerbands_v10c_5_mins/{}.pickle'  # date

actual_spot_path = 'nem-pricing-v2/actual_spot_price/{}.pickle'  # date
actual_spot_5_mins_path = 'nem-pricing-v2/actual_spot_price_5_mins/{}.pickle'  # date
actual_dispatch_5_mins_path = 'nem-pricing-v2/actual_dispatch_5_mins/{}.pickle'  # date
actual_operational_demand_path = 'nem-pricing-v2/actual_operational_demand/{}.pickle'  # date
actual_total_demand_5_mins_path = 'nem-pricing-v2/actual_total_demand_5_mins/{}.pickle'  # date
adjusted_total_demand_5_mins_path = 'nem-pricing-v2/adjusted_total_demand_5_mins/{}.pickle'  # date
savvy_demand_path = 'nem-pricing-v2/savvy_demand/{}.pickle'  # date

all_generation_source_info_path = 'nem-pricing-v2/source_information/all_generation_source.pickle'
units_by_fuel_type_info_path = 'nem-pricing-v2/source_information/units_by_fuel.pickle'
all_plants_from_csv_info_path = 'nem-pricing-v2/source_information/all_plants_from_csv.pickle'
all_units_info_in_DUDETAIL_path = 'nem-pricing-v2/source_information/all_units_info_in_DUDETAIL.pickle'  # date
all_units_list_in_offerbands_path = 'nem-pricing-v2/source_information/all_units_list_in_offerbands.pickle'  # date

# S3 assumption excel path
excel_path = 'assumption-excel/{}.xlsx'
template_path = 'template run 188.xlsx'

# nifi sqs url
nifi_sqs_url = "https://sqs.ap-southeast-2.amazonaws.com/000581985601/nifi_test"

# S3 pickle cache path
reference_date_s3_pickle_path = 'reference_date/{}to{}/{}.pickle'  # index
reference_date_s3_folder_format = 'reference_date/{}to{}/'

pv_data_s3_pickle_path = 'cache/{}/pv.pickle'    # assumptions version
pv_forecast_s3_new_pickle_path = 'cache/{}/pv_forecast.pickle'
pv_history_s3_new_pickle_path = 'cache/{}/pv_history.pickle'
new_projects_pickle_path = 'cache/{}/new_projects.pickle'
retirement_s3_pickle_path = 'cache/{}/retirement.pickle'
demand_growth_rate_s3_pickle_path = 'cache/{}/demand_growth_rate.pickle'
renewable_proportion_s3_pickle_path = 'cache/{}/renewable_proportion.pickle'
small_battery_capacity_s3_pickle_path = 'cache/{}/small_battery_capacity.pickle'
strategic_behaviour_s3_pickle_path = 'cache/{}/strategic_behaviour.pickle'
projects_gen_data_s3_pickle_path = 'cache/{}/historical_generation/{}.pickle'    # assumptions version, date

parameters_for_batch = 'cache/{}/parameters_for_batch.pickle'
parameters_for_batch_v2 = 'cache/{}/parameters_for_batch_test2.pickle'

existing_generation_s3_pickle_path = 'cache/{}/{}/existing.pickle'
new_power_stations_s3_pickle_path = 'cache/{}/{}/new_power_stations.pickle'    # assumptions version, state
negative_adjustment_s3_pickle_path = 'cache/{}/{}/negatives.pickle'    # assumptions version, state
gas_price_escalation_s3_pickle_path = 'cache/{}/{}/escalation.pickle'    # assumptions version, state

# Results path
result_lp_s3_pickle_path = 'result-spot-price-simulation-lp/{}/{}/{}.pickle'  # sim_tag, sim_index, date

nem_price_s3_pickle_path = 'result-spot-price-simulation-lp/{}/{}/SUMMARY.pickle'  # sim_tag, sim_index, date
escalated_price_s3_pickle_path = 'result-spot-price-simulation-lp/{}/{}/nem_price_escalated.pickle'  # sim_tag, sim_index
cpt_revised_price_s3_pickle_path = 'result-spot-price-simulation-lp/{}/{}/nem_price_cpt_revised.pickle'  # sim_tag, sim_index
nem_price_stats_s3_pickle_path = 'result-spot-price-simulation-lp/{}/{}/nem_price_stats.pickle'  # sim_tag, sim_index
nem_price_distribution_s3_pickle_path = 'result-spot-price-simulation-lp/{}/{}/nem_price_distribution.pickle'  # sim_tag, sim_index

ad_hoc_results_for_westwind = 'projects/WestWind/adhoc/{}/{}/dispatch_spot_hh_sims.pickle'  # sim_tag, sim_index

# simulation_tag = 'Run_126'

# New Generator Probabilistic Arrivals
p_dic = {'Committed': [0.5, 0.75, 0.85, 0.9, 0.93, 0.95, 1],
         'Accredited': [0.05, 0.15, 0.35, 0.6, 0.75, 0.8, 1],
         'Proposed': [0.05, 0.1, 0.2, 0.35, 0.45, 0.5, 1]}
d_dic = {'Committed': [0, 3, 6, 12, 18, 24, 360],
         'Accredited': [0, 3, 6, 12, 18, 24, 360],
         'Proposed': [0, 3, 6, 12, 18, 24, 360]}
cf_dic = {'Committed': 0.8,
          'Accredited': 0.6,
          'Proposed': 0.2}

# temporary revise list, should consider a better way to process and store as an assumption
import datetime
revise_list = [{'DUID': 'YWPS1', 'From': datetime.date(2021, 1, 1), 'To': datetime.date(2099, 12, 31), 'MinPrice': 5, 'MaxPrice': 30, 'RevisedPrice': 30.0}, {'DUID': 'YWPS1', 'From': datetime.date(2021, 1, 1), 'To': datetime.date(2099, 12, 31), 'MinPrice': 30, 'MaxPrice': 50, 'RevisedPrice': 45.0}, {'DUID': 'YWPS2', 'From': datetime.date(2021, 1, 1), 'To': datetime.date(2099, 12, 31), 'MinPrice': 5, 'MaxPrice': 30, 'RevisedPrice': 31.0}, {'DUID': 'YWPS2', 'From': datetime.date(2021, 1, 1), 'To': datetime.date(2099, 12, 31), 'MinPrice': 30, 'MaxPrice': 50, 'RevisedPrice': 46.0}, {'DUID': 'YWPS3', 'From': datetime.date(2021, 1, 1), 'To': datetime.date(2099, 12, 31), 'MinPrice': 5, 'MaxPrice': 30, 'RevisedPrice': 32.0}, {'DUID': 'YWPS3', 'From': datetime.date(2021, 1, 1), 'To': datetime.date(2099, 12, 31), 'MinPrice': 30, 'MaxPrice': 50, 'RevisedPrice': 47.0}, {'DUID': 'YWPS4', 'From': datetime.date(2021, 1, 1), 'To': datetime.date(2099, 12, 31), 'MinPrice': 5, 'MaxPrice': 30, 'RevisedPrice': 33.0}, {'DUID': 'YWPS4', 'From': datetime.date(2021, 1, 1), 'To': datetime.date(2099, 12, 31), 'MinPrice': 30, 'MaxPrice': 50, 'RevisedPrice': 48.0}, {'DUID': 'LYA1', 'From': datetime.date(2021, 1, 1), 'To': datetime.date(2099, 12, 31), 'MinPrice': 5, 'MaxPrice': 30, 'RevisedPrice': 28.5}, {'DUID': 'LYA1', 'From': datetime.date(2021, 1, 1), 'To': datetime.date(2099, 12, 31), 'MinPrice': 30, 'MaxPrice': 50, 'RevisedPrice': 43.5}, {'DUID': 'LYA2', 'From': datetime.date(2021, 1, 1), 'To': datetime.date(2099, 12, 31), 'MinPrice': 5, 'MaxPrice': 30, 'RevisedPrice': 29.5}, {'DUID': 'LYA2', 'From': datetime.date(2021, 1, 1), 'To': datetime.date(2099, 12, 31), 'MinPrice': 30, 'MaxPrice': 50, 'RevisedPrice': 44.5}, {'DUID': 'LYA3', 'From': datetime.date(2021, 1, 1), 'To': datetime.date(2099, 12, 31), 'MinPrice': 5, 'MaxPrice': 30, 'RevisedPrice': 30.5}, {'DUID': 'LYA3', 'From': datetime.date(2021, 1, 1), 'To': datetime.date(2099, 12, 31), 'MinPrice': 30, 'MaxPrice': 50, 'RevisedPrice': 45.5}, {'DUID': 'LYA4', 'From': datetime.date(2021, 1, 1), 'To': datetime.date(2099, 12, 31), 'MinPrice': 5, 'MaxPrice': 30, 'RevisedPrice': 31.5}, {'DUID': 'LYA4', 'From': datetime.date(2021, 1, 1), 'To': datetime.date(2099, 12, 31), 'MinPrice': 30, 'MaxPrice': 50, 'RevisedPrice': 46.5}, {'DUID': 'LOYYB1', 'From': datetime.date(2021, 1, 1), 'To': datetime.date(2099, 12, 31), 'MinPrice': 5, 'MaxPrice': 30, 'RevisedPrice': 29.0}, {'DUID': 'LOYYB1', 'From': datetime.date(2021, 1, 1), 'To': datetime.date(2099, 12, 31), 'MinPrice': 30, 'MaxPrice': 50, 'RevisedPrice': 44.0}, {'DUID': 'LOYYB2', 'From': datetime.date(2021, 1, 1), 'To': datetime.date(2099, 12, 31), 'MinPrice': 5, 'MaxPrice': 30, 'RevisedPrice': 30.0}, {'DUID': 'LOYYB2', 'From': datetime.date(2021, 1, 1), 'To': datetime.date(2099, 12, 31), 'MinPrice': 30, 'MaxPrice': 50, 'RevisedPrice': 45.0}]
