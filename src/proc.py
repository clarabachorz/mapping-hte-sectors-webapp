import calc.calc_costs as calc_costs
import pandas as pd
import numpy as np
from calc.calc_costs import calc_LCO_breakdown, calc_all_LCO_wbreakdown, breakdown_LCO_comps
import matplotlib

#initiate with same parameters as load.py
previous_inputs = {'h2_LCO': 70.0,
        'co2_LCO': 300.0,
        'co2ts_LCO': 15.0}

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

    # Obtain full_hm_df. If CO2ts params have been changed, recalculate hm data accordingly
    if inputs["params"]["co2ts_LCO"] != previous_inputs["co2ts_LCO"]:
        print("CO2TS changed")
        print(inputs["params"]["co2ts_LCO"])
        full_hm_df = recalc_hm_df(inputs)
        #save the new full_hm_df
        inputs['full_hm_df'] = full_hm_df
    else:
        full_hm_df = inputs['full_hm_df']

    # filter the full hm df
    selected_sector = inputs["selected_sector"]
    selected_case = inputs["selected_case"]
    df_final = full_hm_df[(full_hm_df["sector"] == selected_sector)&(full_hm_df["scenario"] == selected_case)]

    #take the 4 different dfs needed
    heatmap_df = df_final.pivot(index="h2_LCO", columns="co2_LCO", values="type_ID")
    contour_df = df_final.pivot(index="h2_LCO", columns="co2_LCO", values="fscp")
    hm_transparency_df = df_final.pivot(index="h2_LCO", columns="co2_LCO", values="delta_fscp")
    optioninfo_df = df_final.pivot(index="h2_LCO", columns="co2_LCO", values="code")
    #heatmap data to outputs
    outputs['heatmap_df'] = heatmap_df
    outputs['contour_df'] = contour_df
    outputs['hm_transparency_df'] = hm_transparency_df
    outputs['optioninfo_df'] = optioninfo_df

    #save inputs
    previous_inputs = inputs["params"].copy()


def recalc_hm_df(inputs:dict):
    """Recalculates hm_df based on new co2 transport and storage cost given

    Args:
        inputs (dict): Input parameters determined by the user
    
    Returns;
        full_hm_df: df containing the updated data for the heatmap
    """
    old_hm_df = inputs['full_hm_df']

    #do something
    



    

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


