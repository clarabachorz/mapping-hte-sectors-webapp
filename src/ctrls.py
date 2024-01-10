from dash import dcc, html
import dash_bootstrap_components as dbc


# define input fields with IDs and names
input_fields = {
    'h2-cost': 'Hydrogen supply cost (EUR/MWh)',
    'co2-cost': 'CO₂ supply cost (EUR/t)',
    'co2ts-cost': 'CO₂ transport and storage cost (EUR/t)',
}


# create main control card
def main_ctrl(default_inputs: dict):
    return [html.Div(
        id='simple-controls-card',
        children=[
            html.Div([
                    item
                    for input_field_id, input_field_name in input_fields.items()
                    for item in (
                        dbc.Label(
                            input_field_name,
                            html_for=f"simple-{input_field_id}",
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
                    html.Button(id='simple-update', n_clicks=0, children='GENERATE', className='btn btn-primary'),
                ],
                className='card-element',
            ),
        ],
        className='side-card',
    )]
