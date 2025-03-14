from src.ctrls import input_fields
from dash import callback_context

# update callback function
def update_inputs(inputs_updated: dict, btn_pressed: str,  args: list):#btn_pressed_heatmap: str,
    ctx = callback_context
    #no update if no button pressed
    if not ctx.triggered or ctx.triggered[0]['value'] is None:
        return inputs_updated

    inputs_updated['trigger_id'] = ctx.triggered[0]['prop_id']
    inputs_updated['co2ts-LCO-hm'] = args[5]
    inputs_updated['selected_case'] = args[6]
    inputs_updated['ccu_attribution'] = args[7]

    #for capex table, need to extract the capex values from the dictionnaries
    inputs_updated['steel_capex'] = [entry['steel_capex_value'] for entry in args[8]]

    #to change
    for input_field_id in input_fields:
        param_name = input_field_id.removeprefix('simple-').replace('-', '_')
        inputs_updated['params'][param_name] = args[list(input_fields).index(input_field_id)+2]

    
