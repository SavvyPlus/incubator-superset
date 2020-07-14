import random
from .util import write_pickle_to_s3, read_pickle_from_s3, get_full_week_end_date
from .simulation_config import reference_date_s3_pickle_path, parameters_for_batch, bucket_inputs, \
    parameters_for_batch_v2


def get_reference_day_dict(simulation, index):
    start_date, end_date = simulation.start_date, get_full_week_end_date(simulation.start_date, simulation.end_date)
    ref_dic_t = read_pickle_from_s3(bucket_inputs, reference_date_s3_pickle_path.format(start_date.strftime('%Y-%m-%d'),
                                                                                        end_date.strftime('%Y-%m-%d'),
                                                                                        index))
    ref_dic = dict()
    for key in ref_dic_t:
        ref_date_index = random.randint(0, len(ref_dic_t[key]) - 1)
        ref_dic[key] = ref_dic_t[key][ref_date_index]
    return ref_dic


def generate_parameters_for_batch(simulation, sim_num):
    parameter_dic = dict()
    # random_number = random.randint(0, 49)
    # sim_ref = get_reference_day_dict(random_number)
    sim_tag = simulation.run_id
    for i in range(sim_num):
        parameter_dic[i] = []
        random_number = random.randint(0, sim_num - 1)
        sim_ref = get_reference_day_dict(simulation, random_number)
        sim_date = list(sim_ref.keys())
        ref_date = list(sim_ref.values())
        num_weeks = len(sim_date) / 7
        for j in range(int(num_weeks)):
            week_tmp = []
            for k in range(7):
                tmp_dict = {'sim_date': sim_date[k + 7 * j],
                            'ref_date': ref_date[k + 7 * j]}
                week_tmp.append(tmp_dict)
            parameter_dic[i].append(week_tmp)
        print(i)
    print(write_pickle_to_s3(parameter_dic, bucket_inputs, parameters_for_batch_v2.format(sim_tag)))

