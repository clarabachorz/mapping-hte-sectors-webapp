from calc.calc_costs import calc_LCO_breakdown


# process inputs into outputs
def process_inputs(inputs: dict, outputs: dict):
    outputs['df'] = calc_LCO_breakdown(**inputs['params'])
