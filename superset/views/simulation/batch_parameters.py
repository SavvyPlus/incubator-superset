import random
from .util import write_pickle_to_s3, read_pickle_from_s3
from .simulation_config import bucket_test, reference_date_s3_pickle_path, parameters_for_batch, bucket_inputs, \
    parameters_for_batch_v2


def get_reference_day_dict(index):
    ref_dic_t = read_pickle_from_s3(bucket_inputs, reference_date_s3_pickle_path.format(index))
    ref_dic = dict()
    for key in ref_dic_t:
        ref_date_index = random.randint(0, len(ref_dic_t[key]) - 1)
        ref_dic[key] = ref_dic_t[key][ref_date_index]
    return ref_dic


def generate_parameters_for_batch(sim_tag, sim_num):
    parameter_dic = dict()
    random_number = random.randint(0, 49)
    sim_ref = get_reference_day_dict(random_number)
    # structure #1
    # for i in range(sim_num):
    #     parameter_dic[i] = dict()
    #     sim_date = sim_ref.keys()
    #     ref_date = sim_ref.values()
    #     parameter_dic[i] = dict(zip(sim_date, ref_date))
    #     print(i)
    # structure #2
    for i in range(sim_num):
        sim_date = list(sim_ref.keys())
        ref_date = list(sim_ref.values())
        for j in range(len(sim_date)):
            parameter_dic[(j + 1) + len(sim_date) * i] = {'sim_index': i,
                                                          'sim_date': sim_date[j],
                                                          'ref_date': ref_date[j]}
        print(i)
    write_pickle_to_s3(parameter_dic, bucket_test, parameters_for_batch_v2.format(sim_tag))

