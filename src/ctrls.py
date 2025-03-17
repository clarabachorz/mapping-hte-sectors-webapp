from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc


# define input fields with IDs and names
input_fields = {
    'h2-LCO': 'Low-emission hydrogen cost (EUR/MWh)',
    'co2-LCO': 'Non-fossil CO₂ cost (EUR/t)',
    'co2ts-LCO': 'CO₂ transport and storage cost (EUR/t)',
}

#define drop down options
dropdown_options_sectors = [
    {'label': 'Steel', 'value': 'steel'},
    {'label': 'Maritime', 'value': 'ship'},
    {'label': 'Aviation', 'value': 'plane'},
    {'label': 'Cement', 'value': 'cement'},
    {'label': 'Chemicals', 'value': 'chem'},
]

dropdown_options_case = [
    {'label': 'No conditions', 'value': 'normal'},
    {'label': 'CCU coupling', 'value': 'ccu'},
    {'label': 'Full climate neutrality', 'value': 'comp'},
]

steel_capex_types = ["BF-BOF", "CCS for a BF-BOF", "DRI-EAF"]
steel_capex_units = ["€/t", "€/t", "€/t"]

#create dropdown
def main_ctrl(default_inputs: dict):

    #capex values
    steel_capex_values = default_inputs.get("steel_capex_simple", [684, 196, 556])
    #data table
    simple_steel_capex_table_data = [
        {"steel_capex_type": steel_capex_types[i], "steel_capex_value": steel_capex_values[i], "steel_capex_unit": steel_capex_units[i]}
        for i in range(len(steel_capex_types))
    ]
    
    return [html.Div(
        id='card-ctrl-simple',
        children=[
            html.Div([
                    item
                    for input_field_id, input_field_name in input_fields.items()
                    for item in (
                        html.Label(
                            input_field_name,
                            htmlFor=f"simple-{input_field_id}",
                        ),
                        dcc.Input(
                            id=f"simple-{input_field_id}",
                            type='number',
                            placeholder='Number',
                            value=default_inputs['params'][input_field_id.removeprefix('simple-').replace('-', '_')]
                        ),
                    )
                ],
                className='card-element',
            ),
            html.Div(
                children = [
                        html.Label('CCU attribution (to the user sector)',
                            htmlFor=f"simple-ccu-attr",
                        ),
                        dcc.Input(
                            id=f"simple-ccu-attr",
                            type='number',
                            placeholder='Number',
                            value=default_inputs.get('ccu_attribution', 0.5),
                            min = 0,
                            max = 1,
                            step = 0.01
                    ),
                ],
                className='card-element',
            ),
            html.Div(
                children=[
                    html.Label("Steel CAPEX Table (before annualization)"),
                    dash_table.DataTable(
                        id="simple-steel-capex-table",
                        columns=[
                            {"name": "Technology", "id": "steel_capex_type", "editable": False},
                            {"name": "CAPEX Value", "id": "steel_capex_value", "type": "numeric", "editable": True},
                            {"name": "Unit", "id": "steel_capex_unit", "editable": False},
                        ],
                        data=simple_steel_capex_table_data,
                        editable=True,
                        style_table={"width": "100%"},
                        style_cell={"textAlign": "left"},
                    ),
                ],
                className='card-element',
            ),
            html.Div(
                children=[
                    html.Button(id='simple-update', n_clicks=0, children='GENERATE', className='btn btn-primary'),
                ],
                className='card-element',
            ),
        ],
        className='side-card',
    )]


def hm_ctrl(default_inputs: dict):
    #capex values
    steel_capex_values = default_inputs.get("steel_capex", [684, 196, 556])
    #data table
    steel_capex_table_data = [
        {"steel_capex_type": steel_capex_types[i], "steel_capex_value": steel_capex_values[i], "steel_capex_unit": steel_capex_units[i]}
        for i in range(len(steel_capex_types))
    ]

    return [html.Div(
        id='card-ctrl-heatmap',
        children=[
            html.P(
                "This card allows you to control various parameters for the mitigation landscapes."+
                " Loading the landscapes after changing parameters below takes up to 45 seconds.",
                className='explanation'
            ),
            #co2 transport and storage cost
            html.Div(
                children = [
                        html.Label('CO₂ transport and storage cost (EUR/t)',
                            htmlFor=f"co2ts-LCO-hm",
                        ),
                        dcc.Input(
                            id=f"co2ts-LCO-hm",
                            type='number',
                            placeholder='Number',
                            value=default_inputs.get('co2ts-LCO-hm', 15)
                    ),
                ],
                className='card-element',
            ),

            html.Div(
                children=[
                    html.Label("Select case to plot", htmlFor="dropdown-case"),
                    dcc.Dropdown(
                        id="dropdown-case",
                        options=dropdown_options_case,
                        placeholder="Choose an option",
                        value=default_inputs.get('selected_case', 'normal')
                    ),
                ],
                className='card-element',
            ),

            #ccu attribution
            html.Div(
                children = [
                        html.Label('CCU attribution',
                            htmlFor=f"ccu-attr-hm",
                        ),
                        dcc.Input(
                            id=f"ccu-attr-hm",
                            type='number',
                            placeholder='Number',
                            value=default_inputs.get('ccu_attribution', 0.5),
                            min = 0,
                            max = 1,
                            step = 0.01
                    ),
                ],
                className='card-element',
            ),
            html.Div(
                children=[
                    html.Label("Steel CAPEX Table (before annualization)"),
                    dash_table.DataTable(
                        id="steel-capex-table",
                        columns=[
                            {"name": "Technology", "id": "steel_capex_type", "editable": False},
                            {"name": "CAPEX Value", "id": "steel_capex_value", "type": "numeric", "editable": True},
                            {"name": "Unit", "id": "steel_capex_unit", "editable": False},
                        ],
                        data=steel_capex_table_data,
                        editable=True,
                        style_table={"width": "100%"},
                        style_cell={"textAlign": "left"},
                    ),
                ],
                className='card-element',
            ),
            html.Div(
                children=[
                    html.Button(id='heatmap-update', n_clicks=0, children='GENERATE', className='btn btn-primary'),
                ],
                className='card-element',
            ),
        ],
        className='side-card',
    )]