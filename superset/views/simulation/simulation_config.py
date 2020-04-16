# basic settings for simulation
weather_history_start = "2011-01-01"
# weather_history_end = "2019-12-31"
weather_history_end = "2018-12-31"
start_date_str = "2017-01-01"
# end_date_str = "2019-12-31"
end_date_str = "2018-12-31"
sim_start_date_str = "2017-01-01"
sim_end_date_str = "2028-01-01"
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

actual_spot_path = 'nem-pricing-v2/actual_spot_price/{}.pickle'  # date
actual_spot_5_mins_path = 'nem-pricing-v2/actual_spot_price_5_mins/{}.pickle'  # date
actual_dispatch_5_mins_path = 'nem-pricing-v2/actual_dispatch_5_mins/{}.pickle'  # date
actual_operational_demand_path = 'nem-pricing-v2/actual_operational_demand/{}.pickle'  # date
actual_total_demand_5_mins_path = 'nem-pricing-v2/actual_total_demand_5_mins/{}.pickle'  # date
savvy_demand_path = 'nem-pricing-v2/savvy_demand/{}.pickle'  # date

all_generation_source_info_path = 'nem-pricing-v2/source_information/all_generation_source.pickle'
all_plants_from_csv_info_path = 'nem-pricing-v2/source_information/all_plants_from_csv.pickle'
all_units_info_in_DUDETAIL_path = 'nem-pricing-v2/source_information/all_units_info_in_DUDETAIL.pickle'  # date
all_units_list_in_offerbands_path = 'nem-pricing-v2/source_information/all_units_list_in_offerbands.pickle'  # date

# S3 pickle cache path
reference_date_s3_pickle_path = 'reference_date/test_2017to2027/{}.pickle'  # index

pv_data_s3_pickle_path = 'cache/{}/pv.pickle'    # assumptions version
pv_forecast_s3_new_pickle_path = 'cache/{}/pv_forecast.pickle'
pv_history_s3_new_pickle_path = 'cache/{}/pv_history.pickle'
new_projects_pickle_path = 'cache/{}/new_projects.pickle'
retirement_s3_pickle_path = 'cache/{}/retirement.pickle'
demand_growth_rate_s3_pickle_path = 'cache/{}/demand_growth_rate.pickle'
renewable_proportion_s3_pickle_path = 'cache/{}/renewable_proportion.pickle'
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
nem_price_stats_s3_pickle_path = 'result-spot-price-simulation-lp/{}/{}/nem_price_stats.pickle'  # sim_tag, sim_index
nem_price_distribution_s3_pickle_path = 'result-spot-price-simulation-lp/{}/{}/nem_price_distribution.pickle'  # sim_tag, sim_index

simulation_tag = 'Run_126'