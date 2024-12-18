import calc.calc_costs as calc_costs
import pandas as pd
import numpy as np
from calc.calc_costs import calc_LCO_breakdown, calc_all_LCO_wbreakdown, breakdown_LCO_comps
from calc import process_full_df
import multiprocessing as mp
import itertools
import matplotlib


# process inputs into outputs
def process_inputs(inputs: dict, outputs: dict):
    full_df, LCO_breakdown = get_basic_LCOPs(inputs)
    heatmap_df, contour_df, hm_transparency_df = get_heatmap_data(inputs)

    ##add heat map processing here (only getting the data for the resolution determined. Filtering will be carried out in the HeatMap class)

    outputs['full_df'] = full_df
    outputs['full_df_breakdown'] = LCO_breakdown
    #heatmap data
    outputs['heatmap_df'] = heatmap_df
    outputs['contour_df'] = contour_df
    outputs['hm_transparency_df'] = hm_transparency_df
    #advanced breakdown for the sectors, not currently used
    outputs['df_sectors'], outputs['df_fuels'] = breakdown_LCO_comps(LCO_breakdown)

def get_heatmap_data(inputs:dict):
    """Obtain the data for the heatmap

    Args:
        inputs (dict): Input parameters determined by the user

    Returns:
        heatmap_df: df containing the data for the heatmap
    """
    #define heatmap resolution
    param_dict = {
        "h2_LCO": np.arange(0, 242, 2),  # used to be 2
        "co2_LCO": np.arange(0, 1225, 25),  # used to be 25
        "co2ts_LCO": [15],    
    }

    params = itertools.product(*param_dict.values())

    with mp.Pool(mp.cpu_count()) as pool:
        mainfig_list_of_dfs = pool.starmap(heatmap_calc_dfs, [(param_set, param_dict) for param_set in params])
    
    list_of_dfs = [df for sublist in mainfig_list_of_dfs for df in sublist]  # Flatten the list
    df_final = pd.concat(list_of_dfs, ignore_index=True)

    #make discrete heat map by assigning a "type ID" to each technology
    dict_type_ID = {"h2": 0, "efuel": 0.25, "comp":0.5, "ccu":0.75, "ccs":1}


    df_final["type_ID"] = df_final["type"].map(dict_type_ID)

    df_final = df_final[df_final["sector"] == "steel"]
    df_final = df_final[df_final["scenario"] == "normal"]

    heatmap_df = df_final.pivot(index="h2_LCO", columns="co2_LCO", values="type_ID")
    contour_df = df_final.pivot(index="h2_LCO", columns="co2_LCO", values="fscp")
    hm_transparency_df = df_final.pivot(index="h2_LCO", columns="co2_LCO", values="delta_fscp")

    return heatmap_df, contour_df, hm_transparency_df

def heatmap_calc_dfs(param_set, param_dict):
    temp_dict = dict(zip(param_dict.keys(), param_set))
    load_json = True

    df_normal = process_full_df.get_df(scenario = "normal", load_json = load_json, **temp_dict)
    df_ccu = process_full_df.get_df(scenario = "ccu", CCU_coupling=True, DACCS = True, compensate=False, load_json= load_json, **temp_dict)
    df_comp = process_full_df.get_df(scenario = "comp", CCU_coupling=True, DACCS=False, compensate=True, load_json=load_json, **temp_dict)

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


