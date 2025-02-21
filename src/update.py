from src.ctrls import input_fields
from dash import callback_context

# update callback function
def update_inputs(inputs_updated: dict, btn_pressed: str, args: list):
    ctx = callback_context

    #no update if no button pressed
    if not ctx.triggered or ctx.triggered[0]['value'] is None:
        return inputs_updated

    inputs_updated['selected_sector'] = args[-3]
    inputs_updated['selected_case'] = args[-2]
    
    for input_field_id in input_fields:
        param_name = input_field_id.removeprefix('simple-').replace('-', '_')
        inputs_updated['params'][param_name] = args[list(input_fields).index(input_field_id)+1]
