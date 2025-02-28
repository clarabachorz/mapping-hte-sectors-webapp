import pandas as pd
import numpy as np
import matplotlib
import multiprocessing as mp
import itertools

import calc.calc_costs as calc_costs
from calc.calc_costs import calc_LCO_breakdown, calc_all_LCO_wbreakdown, breakdown_LCO_comps
from calc import process_full_df
from . import load


#initiate with same parameters as load.py
previous_inputs = {'h2_LCO': load.H2_LCO_DEFAULT,
        'co2_LCO': load.CO2_LCO_DEFAULT,
        'co2ts_LCO': load.CO2TS_LCO_DEFAULT}

# process inputs into outputs
def process_inputs(inputs: dict, outputs: dict):
    #define global variable
    global previous_inputs

    #calculate basic abatement cost annd breakdowns
    full_df, LCO_breakdown = get_basic_LCOPs(inputs)

    # basic LCOs and breakdown
    outputs['full_df'] = full_df
    outputs['full_df_breakdown'] = LCO_breakdown
    #advanced breakdown for the sectors and fuels
    outputs['df_sectors'], outputs['df_fuels'] = breakdown_LCO_comps(LCO_breakdown)

    # Load inputs
    full_hm_df = inputs['full_hm_df']
    selected_case = inputs["selected_case"]

    # filter the full hm df. If the co2 transport and storage cost has been changed, the heat map data is updated
    # only valid if the hm button has been pressed
    #the if loop also catches the case where both co2ts and ccu have been changed
    if inputs['trigger_id'] == "heatmap-update.n_clicks" and inputs['co2ts-LCO-hm'] != previous_inputs['co2ts_LCO'] or inputs['co2ts-LCO-hm'] != load.CO2TS_LCO_DEFAULT:
        new_hm_df = recalc_hm_df(inputs)
        df_final = new_hm_df
    #also check case where only ccu attribution has been changed, and not co2ts
    elif inputs['trigger_id'] == "heatmap-update.n_clicks" and inputs['ccu_attribution'] != previous_inputs['ccu_attribution'] or inputs['ccu_attribution'] != load.CCU_ATTR_DEFAULT:
        new_hm_df = recalc_hm_df(inputs)
        df_final = new_hm_df
    elif inputs['trigger_id'] == "heatmap-update.n_clicks" and set(inputs['steel_capex']) != set(previous_inputs['steel_capex']) or inputs['steel_capex'] != load.STEEL_CAPEX_DEFAULT:
        new_hm_df = recalc_hm_df(inputs)
        df_final = new_hm_df
    else:
        df_final = full_hm_df[full_hm_df["scenario"] == selected_case]

   

    #take the 4 different dfs needed
    heatmap_df = df_final.pivot(index=["sector", "h2_LCO"], columns="co2_LCO", values="type_ID")
    contour_df = df_final.pivot(index=["sector", "h2_LCO"], columns="co2_LCO", values="fscp")
    hm_transparency_df = df_final.pivot(index=["sector", "h2_LCO"], columns="co2_LCO", values="delta_fscp")
    optioninfo_df = df_final.pivot(index=["sector", "h2_LCO"], columns="co2_LCO", values="code")

    #heatmap data to outputs
    outputs['heatmap_df'] = heatmap_df
    outputs['contour_df'] = contour_df
    outputs['hm_transparency_df'] = hm_transparency_df
    outputs['optioninfo_df'] = optioninfo_df

    #save inputs
    previous_inputs['co2ts_LCO'] = inputs['co2ts-LCO-hm']
    previous_inputs['ccu_attribution'] = inputs['ccu_attribution']
    previous_inputs['steel_capex'] = inputs['steel_capex']



def recalc_hm_df(inputs:dict):
    """Recalculates hm_df based on new co2 transport and storage cost given

    Args:
        inputs (dict): Input parameters determined by the user
    
    Returns;
        full_hm_df: df containing the updated data for the heatmap
    """
    #params are not necessarily updated. if/elif loop catches the correct cases.
    selected_co2ts_LCO = inputs['co2ts-LCO-hm']
    selected_ccu_attr = inputs['ccu_attribution']
    selected_case = inputs["selected_case"]

    #capex
    bf_bof_capex = inputs['steel_capex'][0]
    ccs_capex = inputs['steel_capex'][1]
    dri_eaf_capex = inputs['steel_capex'][2]

    param_dict = {
        "h2_LCO": np.arange(0, 245, 5),  # used to be 2
        "co2_LCO": np.arange(0, 1250, 50),  # used to be 25
        "co2ts_LCO": [selected_co2ts_LCO],
        "co2ccu_co2em": [selected_ccu_attr],
        "fossil_steel_capex": [bf_bof_capex],
        "comp_steel_capex": [bf_bof_capex],
        "ccs_steel_capex": [bf_bof_capex + ccs_capex],
        "ccu_steel_capex": [bf_bof_capex + ccs_capex],
        "h2_steel_capex": [dri_eaf_capex],
    }

    params = itertools.product(*param_dict.values())

    with mp.Pool(mp.cpu_count()) as pool:
        list_of_dfs = pool.starmap(heatmap_recalc_dfs, [(param_set, param_dict, selected_case) for param_set in params])
    
    df_final = pd.concat(list_of_dfs, ignore_index=True)

    #make discrete heat map by assigning a "type ID" to each technology
    dict_type_ID = {"h2": 0, "efuel": 0.25, "comp":0.5, "ccu":0.75, "ccs":1}
    df_final["type_ID"] = df_final["type"].map(dict_type_ID)

    return df_final
    
def heatmap_recalc_dfs(param_set, param_dict, scenario):
    """Compute heatmap data for a given case/scenario

    Args:
        param_set (tuple): Parameter values to use
        param_dict (dict): Parameter dictionary
        scenario (str): The scenario/case to compute

    Returns:
        pd.DataFrame: The calculated heatmap dataframe
    """
    temp_dict = dict(zip(param_dict.keys(), param_set))
    load_json = True
    if scenario == "normal":
        return process_full_df.get_df(scenario = "normal", load_json = load_json, **temp_dict)
    elif scenario == "ccu":
        return process_full_df.get_df(scenario = "ccu", CCU_coupling=True, DACCS = True, compensate=False, load_json= load_json, **temp_dict)
    elif scenario == "comp":
        return process_full_df.get_df(scenario = "comp", CCU_coupling=True, DACCS=False, compensate=True, load_json=load_json, **temp_dict)


    return [df_normal, df_ccu, df_comp]


    

def get_basic_LCOPs(inputs:dict):
    """Obtain basic LCOPs for the given set of parameters (currently low-emission H2 cost and non-fossil CO2 cost)

    Args:
        inputs (dict): Input parameters determined by the user

    Returns:
        full_df: Df containing cost, emissions and abatement costs for each mitigation option for each HTE sector
        LCO_breakdown: Df containing the LCO breakdown for each mitigation option for each HTE sector
    """
    full_df, LCO_breakdown = calc_all_LCO_wbreakdown(**inputs['params'])

    # split tech name into type (ccs, ccu, ..) and actual sector
    full_df[["type", "sector"]] = full_df["tech"].str.split("_", expand=True)

    # convert costs for the aviation sector from EUR to cEUR:
    full_df.loc[full_df['sector'] == 'plane', 'cost'] = full_df.loc[full_df['sector'] == 'plane', 'cost'] * 100
    # And for the LCO breakdown
    numeric_cols = LCO_breakdown.select_dtypes(include=[np.number]).columns.tolist()
    numeric_cols.remove('tech') if 'tech' in numeric_cols else None
    LCO_breakdown.loc[LCO_breakdown['tech'].str.contains('plane'), numeric_cols] *= 100

    #all fuel rows in this df have sector = None. Separate them out
    df_fuels = full_df[full_df["sector"].isnull()]

    # groups the dataframe by sector, and calculates all FSCPs.
    df_macc = full_df.groupby("sector", as_index=False, group_keys=False).apply(
        lambda x: calc_costs.calc_FSCP(x)
    )

    #reassemble the dataframe to include the fuel rows
    full_df = pd.concat([df_macc, df_fuels])
    return full_df, LCO_breakdown


