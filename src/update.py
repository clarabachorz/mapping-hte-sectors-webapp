from src.ctrls import input_fields


# update callback function
def update_inputs(inputs_updated: dict, btn_pressed: str, args: list):
    for input_field_id in input_fields:
        param_name = input_field_id.removeprefix('simple-').replace('-', '_')
        inputs_updated['params'][param_name] = args[list(input_fields).index(input_field_id)+1]
