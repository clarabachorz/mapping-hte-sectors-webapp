import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from src.plots.BasePlot import BasePlot
from src.utils import load_yaml_plot_config_file


class FuelStackedBarPlot(BasePlot):
    figs, cfg = load_yaml_plot_config_file('FuelStackedBarPlot')
    _add_subfig_name = True

    def plot(self, inputs: dict, outputs: dict, subfig_names: list) -> dict:
        tech_displayname = pd.Series(outputs['full_df']["code"].values, index = outputs['full_df']["tech"]).to_dict()
        df_fuels = outputs['df_fuels']
        
        nan_counts = df_fuels.isna().sum(axis=1)

        # Filter rows according to number of NaNs
        df_fuels_with_nans = df_fuels[nan_counts >= 22]
        # Filter rows where 'tech' column contains 'fossil'
        df_fuels_fossils = df_fuels_with_nans[df_fuels_with_nans['tech'].str.contains('fossil')]
        df_fuels_fossils = df_fuels_fossils.dropna(axis = 1, how = 'all')
        df_fuels_fossils['cost'] = df_fuels_fossils['LCO']
        #other synfuels
        df_fuels_synfuels = df_fuels[nan_counts < 22]
        #need to drop the ch3oh and heat "total cost" columns, as we double count otherwise
        #df_fuels_synfuels.drop(columns=['ch3oh', 'ch3ohccu', 'heat'], inplace=True)
        df_fuels_synfuels = df_fuels_synfuels.drop(columns=['ch3oh', 'ch3ohccu', 'heat', 'ch3oh_heat', 'ch3ohccu_heat']).sort_values(['LCO'])


        fig = make_subplots(rows=1, cols=2)

        for i, df in enumerate([df_fuels_fossils, df_fuels_synfuels]):
            df_plot = self._prepare(df)
            #df_plot['tech_name'] = df_plot['tech'].map(tech_displayname)
            df_plot['tech_name'] = df_plot['tech'].map({
                var: display['label']
                for var, display in self._glob_cfg['cost_types'].items()
                })

            self._add_bars(fig, i, df_plot)

        fig.update_layout(
        barmode='stack',
        yaxis_title=self.cfg['yaxis_title'],
        legend_title='',
        )

        return{'fig1': fig}
    def _prepare(self, df: pd.DataFrame) -> pd.DataFrame:

        #filter to get the correct columns, and put df in long format
        df_plot = df.drop(columns=['LCO']).melt(id_vars='tech').fillna(0.0)
        
        #here, function that separates variables
        df_plot = self._split_variable_column(df_plot)

        if self._target == 'webapp':
            df_plot['hover_ptype'] = df_plot['variable'].map({
                var: display['label']
                for var, display in self._glob_cfg['cost_types'].items()
            })
            df_plot['hover_ftype'] = df_plot['subvar'].map({
                var: display['label']
                for var, display in self._glob_cfg['cost_types'].items()
            })
            df_plot['display_color'] = df_plot['variable'].map({
                var: display['colour']
                for var, display in self._glob_cfg['cost_types'].items()
            })
            #TO ADD: subcomponents if applicable
            if df_plot['tech'].str.contains('fossil').any():
                df_plot['unit'] = df_plot['tech'].map({
                var: display['unit']
                for var, display in self._glob_cfg['fossils'].items()
            })
                #sort for aesthetic purposes
                df_plot = df_plot.sort_values(['unit', 'value'])
            else:
                df_plot['unit'] = "EUR/MWh"
                #set bar custom order according to global config
                order = self._glob_cfg['cost_types'].keys()
                df_plot['variable'] = df_plot['variable'].astype('category')
                df_plot['variable'] = df_plot['variable'].cat.set_categories(order, ordered=True)
                
                df_plot['subvar'] = df_plot['subvar'].astype('category')
                df_plot['subvar'] = df_plot['subvar'].cat.set_categories(order, ordered=True)
                df_plot = df_plot.sort_values(['variable', 'subvar'])


        

        return df_plot

    def _add_bars(self, fig, i, df_plot):

        hover = self._target == 'webapp'
        hovercols = ['tech_name', 'hover_ptype', 'hover_ftype', 'value', 'unit'] if hover else None
        hovercomp = {
            'header_basic': '<b>%{customdata[0]}</b><br>',
            'var_type':'Component: %{customdata[1]}<br>',
            'subvar':'Subcomponent: %{customdata[2]}<br>',
            'cost':'Cost: %{customdata[3]:.2f} %{customdata[4]}'
        }
        hovertemplate = ''.join(hovercomp[c] for c in ['header_basic', 'var_type', 'subvar', 'cost'])

        hovertemplate = (
            None if not hover else hovertemplate
        )

        # Define your custom legend labels
        legend_labels = {
            'ch3ohccu': 'Fossil CCU based methanol',
            'ch3oh': 'DAC-based methanol',
            'co2': 'CO<sub>2</sub> from DAC',
            'h2': 'Green H<sub>2</sub>',
            'heat': 'Heat',
            'elec': 'Electricity',
            'other costs': 'CAPEX and fixed OPEX',
            'capex': 'CAPEX',
            'opex': 'Fixed OPEX',
            'cost': 'Fossil fuel cost',
        }

        # Some variables have to be grouped together
        grouped_variables = ['capex', 'opex', 'other costs']

        #plot the bars for each variable
        for variable in df_plot['variable'].unique():
            df_variable = df_plot[df_plot['variable'] == variable]
            fig.add_trace(
                go.Bar(
                    x=df_variable['tech_name'], 
                    y=df_variable['value'], 
                    marker_color=df_variable['display_color'],
                    name=legend_labels.get(variable, variable),
                    hoverinfo='text' if hover else 'skip',
                    hovertemplate=hovertemplate,
                    customdata=df_variable[hovercols] if hover else None,
                ),
                row=1, 
                col=i+1
            )

        # fig.add_trace(
        #     go.Bar(
        #         x=df_plot['tech_name'], 
        #         y=df_plot['value'], 
        #         marker_color = df_plot['display_color'],
        #         #name=sector,
        #         #showlegend=not i,
        #         hoverinfo='text' if hover else 'skip',
        #         hovertemplate=hovertemplate,
        #         customdata=df_plot[hovercols] if hover else None,
        #         ),
        #     row=1, 
        #     col=i+1
        #     )
    def _split_variable_column(self, df: pd.DataFrame) -> pd.DataFrame:
        split_df = df['variable'].str.split('_', expand=True)

        df['variable'] = split_df[0]
        df['subvar'] = split_df[1] if split_df.shape[1] > 1 else None
        df['subvar'] = df['subvar'].fillna('NA')

        return df