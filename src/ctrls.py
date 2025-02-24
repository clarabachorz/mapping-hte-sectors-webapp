from dash import dcc, html
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

#create dropdown
def main_ctrl(default_inputs: dict):
    return [html.Div(
        id='simple-controls-card',
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
                children=[
                    html.Label("Select case to plot (Heatmap page only)", htmlFor="dropdown-case"),
                    dcc.Dropdown(
                        id="dropdown-case",
                        options=dropdown_options_case,
                        placeholder="Choose an option",
                        value=default_inputs.get('selected_case', 'normal')
                    ),
                ],
                className='card-element',
            ),

            # Generate Button
            html.Div(
                children=[
                    html.Button(id='simple-update', n_clicks=0, children='GENERATE', className='btn btn-primary'),
                ],
                className='card-element',
            ),
        ],
        className='side-card',
    )]