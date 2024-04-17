import calc.calc_costs as calc_costs
import pandas as pd
import numpy as np
from calc.calc_costs import calc_LCO_breakdown
from calc.calc_costs import calc_all_LCO_wbreakdown
from calc.calc_costs import breakdown_LCO_comps


# process inputs into outputs
def process_inputs(inputs: dict, outputs: dict):
    #outputs['df'] = calc_LCO_breakdown(**inputs['params'])[0]

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

    outputs['full_df'] = full_df
    outputs['full_df_breakdown'] = LCO_breakdown
    #advanced breakdown for the sectors, not currently used
    outputs['df_sectors'], outputs['df_fuels'] = breakdown_LCO_comps(LCO_breakdown)

