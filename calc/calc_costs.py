import numpy as np
import pandas as pd
import itertools
import json
from analysis.common.tech_class import *
import re
import math
from itertools import compress

def calc_all_LCO(
    path_to_params="./analysis/common/params.json",
    get_LCO_comps=False,
    compensate_residual_ems = False,
    ccu_income = False,
    inexistant_techs=[
        "ccs_plane",
        "h2_plane",
        "ccs_ship",
        "efuel_steel",
        "ccs_chem",
        "h2_chem",
        "efuel_cement",
        "h2_cement",
    ],
    **kwargs
):
    user_params = {}
    tech.common_dict = {}
    rows_LCO_comps = []

    for key, value in kwargs.items():
        user_params[key] = value

    # JSON FILE HOLDS ALL EXTERNAL ASSUMPTIONS
    data = json.load(open(path_to_params))

    # initialise the techs using the assumptions from the json file
    for row in data["techs"]:
        temp_dict = {
            k.rsplit("_", 1)[1]: v
            for k, v in user_params.items()
            if k.rsplit("_", 1)[0] == row["key"]
        }
        row.update(temp_dict)
        temp_tech = tech(row, comp = compensate_residual_ems, ccu_income = ccu_income)

        # to get the individual LCO components
        if get_LCO_comps:
            # get the components
            LCO_comps = temp_tech.LCO_comps

            # #add the key parameters that have been changed relative to default
            # #NOT USED RIGHT NOW
            # for key in user_params.keys():
            #     LCO_comps[key] = user_params[key]

            # append the result to a list
            rows_LCO_comps.append(LCO_comps)

    # Get the LCOs that have been calculated
    final_dict = tech.common_dict

    ## add an empty entry for technologies that don't exist (inexistant_techs)
    for i in inexistant_techs:
        type = i.split("_")[0]

        if type == "h2":
            type = "h2/nh3"

        final_dict[i] = [np.nan, np.nan, np.nan, "no " + type, np.nan, np.nan]

    df = to_df_fmt(final_dict)

    for key in user_params.keys():
        df[key] = user_params[key]

    if get_LCO_comps:
        return (df, pd.DataFrame(rows_LCO_comps))
    return df


def to_df_fmt(dict):
    rows = []

    for key in dict.keys():
        row = dict[key]
        row.insert(0, key)
        rows.append(row)

    df = pd.DataFrame(rows, columns=["tech", "cost", "em", "elec", "code", "co2", "co2_comp"]).round(6)
    return df


# get multiple LCOs
def multiple_LCOs(param_dict):
    params = itertools.product(*param_dict.values())

    list_of_dfs = []

    for idx, param_set in enumerate(params):
        # calculate set of parameter
        temp_dict = dict(zip(param_dict.keys(), param_set))

        df = calc_all_LCO(**temp_dict)

        # clean
        df = df[df["tech"].str.contains("plane|ship|steel|chem|cement")]
        # df["type"], df["sector"] = df["tech"].str.split("_", 1).str
        df[["type", "sector"]] = df["tech"].str.split("_", expand=True)

        # calculate fscp
        df = df.groupby("sector", group_keys=False).apply(lambda x: calc_FSCP(x))
        list_of_dfs.append(df)

    df = pd.concat(list_of_dfs)
    return df


# calculate error bars on the LCOs
def calc_uncertainties(**kwargs):
    param_dict = {}

    for key, value in kwargs.items():
        param_dict[key] = value

    # get the full dataframe with all the data
    dfs = multiple_LCOs(param_dict)

    # #calculate statistics
    dfs = dfs.groupby("tech")["fscp"].describe()

    return dfs


def FSCP(green_c, green_em, fossil_c, fossil_em):
    with np.errstate(divide="ignore", invalid="ignore"):
        try:
            if fossil_em > green_em:
                return round((green_c - fossil_c) / (fossil_em - green_em),5)
            # elif green_c < fossil_c:
            #     # cheaper green technology means the fscp is no longer
            #     # well defined.
            #     return np.nan
            else:
                # if the emissions of the green tech are higher than that
                # of the fossil tech, the fscp is not defined
                return np.nan
        except:
            # takes care of divisions by 0 for fscp
            return np.nan


def calc_FSCP(df):
    # identify the fossil tech row, extract row as dict
    fossil_dict = df.loc[df["type"] == "fossil"].to_dict("records")[0]

    # calculate the FSCP
    # df = df.reset_index()
    df["fscp"] = df.apply(
        lambda x: FSCP(x["cost"], x["em"], fossil_dict["cost"], fossil_dict["em"]),
        axis=1,
    )
    df["elec_fscp"] = df.apply(
        lambda x: FSCP(x["elec"], x["em"], fossil_dict["elec"], fossil_dict["em"]),
        axis=1,
    )

    df["co2_comp"] = df.apply(
        lambda x: x["co2_comp"]*100 / fossil_dict["em"],
        axis=1,
    )

    return df

def calc_LCO_breakdown(h2_cost=70, co2_cost=300, co2ts_cost=15):

    df_total, comps = calc_all_LCO(
    get_LCO_comps= True,
    h2_LCO=h2_cost,
    co2_LCO=co2_cost,
    co2ts_LCO=co2ts_cost,
)
    comps.replace(0.0, np.nan, inplace=True)

    new_rows = []
    for index, row in comps.iterrows():
        row_param = row["tech"]
        #here, filter and select only the fuel rows - ignore ship, steel, etc

        if re.search("ship|steel|plane|chem|cement|fossil", row_param):
            pass
        else:
            for index2, row2 in comps.iterrows():
                row2_param = row2["tech"]

                if index == index2:
                    #here, make sure the h2 row does not multiply the h2 row
                    pass
                else:
                    try:
                        #check that row_param is included in row2 AND is not nan
                        if not math.isnan(row2[row_param]):

                            #list with which rows have already been updates
                            updated_params = [x["tech"] for x in new_rows]

                            #checks that row2 contains the parameter being iterated over
                            param_fraction = row2[row_param] / row["LCO"]

                            # Removes tech,LCO row and clean up
                            # the LCO row is already in row2. Redundant info.
                            new_row = row.drop(["tech","LCO"]).convert_dtypes().dropna()
                            
                            new_row = new_row.multiply(param_fraction)


                            # In this loop: check that new_row does not contain params that have previously been broken down
                            # in updated_params. If it does, update new_row
                            
                            if not set(new_row.keys()).isdisjoint(updated_params):
                                
                                #identify the common element and add more parameters to new_row
                                common_subparams = list(set(new_row.keys()).intersection(updated_params))
                            
                                for subparam in common_subparams:
                                    #get the updated series corresponding to the subparam we are interested in
                                    updated_subparam = list(compress(new_rows, [x["tech"] == subparam for x in new_rows]))[0]
                                    subparam_fraction = new_row[subparam] / updated_subparam["LCO"]

                                    #clean, remove useless columns, convert to correct dtype
                                    new_subrow = updated_subparam.drop(["tech","LCO"]).convert_dtypes().dropna()
                                    
                                    # scale the row usiing the subparam fraction
                                    new_subrow = new_subrow.multiply(subparam_fraction)
                                    
                                    # rename the new rows for clariy
                                    new_subrow = new_subrow.add_prefix(subparam + "_")
                                    
                                    # add the results to the row we are working with
                                    new_row = pd.concat([new_row, new_subrow])
                                    

                            else:
                                pass
                            new_row = new_row.add_prefix(row_param + "_")
                            new_row = pd.concat([row2, new_row])

                            
                            #here, we add a loop which check whether the entry already exists in the new rows list. If so, update it.
                            if row2_param not in updated_params:
                                new_rows.append(new_row)
                            else:
                                for idx, item in enumerate(new_rows):
                                    if row2_param == item["tech"]:
                                        
                                        #here, item and new row have to be updated and combined
                                        new_row = item.combine_first(new_row)
                                        new_rows[idx] = new_row
                        else:
                            pass
                            
                    except:
                        pass

    new_LCO_comps = pd.concat(new_rows, axis = 1).transpose().set_index("tech")
    comps.set_index("tech", inplace=True)

    #merge: updated_LCO now contains all the details we want !
    updated_LCO = new_LCO_comps.combine_first(comps).dropna(axis=1, how='all')

    sectors_LCO = updated_LCO.filter(regex=r'(plane|ship|cement|chem|steel)', axis = 0).reset_index()

    df_all = updated_LCO.reset_index().merge(sectors_LCO.drop_duplicates(), on=None, 
                    how='left', indicator=True)

    fuel_LCO = df_all[df_all["_merge"] == "left_only"].drop("_merge", axis = 1).dropna(axis=1, how='all').set_index("tech")

    return(sectors_LCO)
