from src.ctrls import input_fields
from dash import callback_context

# update callback function
def update_inputs(inputs_updated: dict, btn_pressed: str,  args: list):
    ctx = callback_context
    #no update if no button pressed
    if not ctx.triggered or ctx.triggered[0]['value'] is None:
        return inputs_updated

    inputs_updated['trigger_id'] = ctx.triggered[0]['prop_id']

    for input_field_id in input_fields:
        param_name = input_field_id.removeprefix('simple-').replace('-', '_')
        inputs_updated['params'][param_name] = args[list(input_fields).index(input_field_id)+2]
    
    inputs_updated['ccu_attribution_simple'] = args[5]
    inputs_updated['steel_capex_simple'] = [entry['steel_capex_value'] for entry in args[6]]
    inputs_updated['co2ts-LCO-hm'] = args[7]
    inputs_updated['selected_case'] = args[8]
    inputs_updated['ccu_attribution'] = args[9]

    #for capex table, need to extract the capex values from the dictionnaries
    inputs_updated['steel_capex'] = [entry['steel_capex_value'] for entry in args[10]]

    
