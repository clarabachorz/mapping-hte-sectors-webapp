from calc import process_full_df
import multiprocessing as mp
import itertools
import matplotlib
import numpy as np
import pandas as pd
import time


#initial params
H2_LCO_DEFAULT = 70.0
CO2_LCO_DEFAULT = 300.0
CO2TS_LCO_DEFAULT = 15.0

def define_inputs(inputs: dict):
    inputs['params'] = {
        'h2_LCO': H2_LCO_DEFAULT,
        'co2_LCO': CO2_LCO_DEFAULT,
        'co2ts_LCO': CO2TS_LCO_DEFAULT,
    }
    inputs['selected_sector'] = 'steel'
    inputs['selected_case'] = 'normal'

    inputs['full_hm_df'] = get_heatmap_data()


def get_heatmap_data():
    """Obtain the data for the heatmap

    Args:
        inputs (dict): Input parameters determined by the user

    Returns:
        heatmap_df: df containing the data for the heatmap
    """
    #define heatmap resolution
    param_dict = {
        "h2_LCO": np.arange(0, 245, 5),  # used to be 2
        "co2_LCO": np.arange(0, 1300, 100),  # used to be 25
        "co2ts_LCO": [CO2TS_LCO_DEFAULT],    
    }

    params = itertools.product(*param_dict.values())

    with mp.Pool(mp.cpu_count()) as pool:
        mainfig_list_of_dfs = pool.starmap(heatmap_calc_dfs, [(param_set, param_dict) for param_set in params])
    
    list_of_dfs = [df for sublist in mainfig_list_of_dfs for df in sublist]  # Flatten the list
    df_final = pd.concat(list_of_dfs, ignore_index=True)

    #make discrete heat map by assigning a "type ID" to each technology
    dict_type_ID = {"h2": 0, "efuel": 0.25, "comp":0.5, "ccu":0.75, "ccs":1}
    df_final["type_ID"] = df_final["type"].map(dict_type_ID)
    print(df_final[df_final["scenario"] == "normal"])
    print(df_final[df_final["scenario"] == "normal"].columns)
    return df_final

def heatmap_calc_dfs(param_set, param_dict):
    temp_dict = dict(zip(param_dict.keys(), param_set))
    load_json = True

    df_normal = process_full_df.get_df(scenario = "normal", load_json = load_json, **temp_dict)
    df_ccu = process_full_df.get_df(scenario = "ccu", CCU_coupling=True, DACCS = True, compensate=False, load_json= load_json, **temp_dict)
    df_comp = process_full_df.get_df(scenario = "comp", CCU_coupling=True, DACCS=False, compensate=True, load_json=load_json, **temp_dict)


    return [df_normal, df_ccu, df_comp]

