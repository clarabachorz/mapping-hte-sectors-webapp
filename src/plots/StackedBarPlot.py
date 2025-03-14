import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from src.plots.BasePlot import BasePlot
from src.utils import load_yaml_plot_config_file


class StackedBarPlot(BasePlot):
    figs, cfg = load_yaml_plot_config_file('StackedBarPlot')
    _add_subfig_name = True

    sectors = [ "chem", "plane","ship", "steel", "cement"]

    def plot(self, inputs: dict, outputs: dict, subfig_names: list) -> dict:
        tech_displayname = pd.Series(outputs['full_df']["code"].values, index = outputs['full_df']["tech"]).to_dict()

        df = outputs['full_df_breakdown']

        df = df[df.index.to_series().str.contains('|'.join(self.sectors))].reset_index()
        df[["type", "sector"]] = df["tech"].str.split("_", expand=True)
        df = df.drop(df[df['tech']=='h2_plane'].index)
        
        subplot_titles = [self._glob_cfg['sector'][sector]['label'] for sector in self.sectors]
        fig = make_subplots(rows=1, cols=5, 
                            subplot_titles=subplot_titles)

        for i,sector in enumerate(self.sectors):
            df_plot = self._prepare(df, sector)

            df_plot['tech_name'] = df_plot['tech'].map(tech_displayname)
            self._add_bars(fig, i, sector, df_plot)
            # fig.add_trace(go.Bar(x=df_plot['tech'], y=df_plot['value'], name=df_plot['variable']), row=1, col=i+1)#, marker_color = df_plot['variable']
            
        fig.update_xaxes(tickfont=dict(size=8))
        fig.update_layout(
        barmode='stack',
        yaxis_title=self.cfg['yaxis_title'],
        legend_title='',
        legend=dict(
            yanchor="bottom",
            y=1.15,  # puts legend below the plot
            xanchor="center",
            x=0.5,
            orientation="h"  # makes the legend horizontal
        ),
        margin=dict(l=0, r=0, t=50, b=250),
        )

        return {'fig2': fig}
    
    def _prepare(self, df: pd.DataFrame, sector: str) -> pd.DataFrame:

        #filter to get the correct sector, and put df in long format
        df_plot = df[df["sector"]==sector]
        df_plot = df_plot.drop(columns=['LCO', 'type', 'sector']).melt(id_vars='tech')
        df_plot = df_plot.fillna(0.0)


        if self._target == 'webapp':
            df_plot['hover_ptype'] = df_plot['variable'].map({
                var: display['label']
                for var, display in self._glob_cfg['cost_types'].items()
            })
            df_plot['display_color'] = df_plot['variable'].map({
                var: display['colour']
                for var, display in self._glob_cfg['cost_types'].items()
            })
            df_plot['unit'] = self._glob_cfg['sector'][sector]['unit']
        
        #set bar custom order according to global config
        order = self._glob_cfg['cost_types'].keys()
        df_plot['variable'] = df_plot['variable'].astype('category')
        df_plot['variable'] = df_plot['variable'].cat.set_categories(order, ordered=True)
        df_plot = df_plot.sort_values(['variable'])

        return df_plot

    def _add_bars(self, fig, i, sector, df_plot):

        hover = self._target == 'webapp'
        hovercols = ['tech_name', 'hover_ptype', 'value', 'unit'] if hover else None
        hovercomp = {
            'header_basic': '<b>%{customdata[0]}</b><br>',
            'var_type':'Component: %{customdata[1]}<br>',
            'cost':'Cost: %{customdata[2]:.2f} %{customdata[3]}'
        }
        hovertemplate = ''.join(hovercomp[c] for c in ['header_basic', 'var_type', 'cost'])

        hovertemplate = (
            None if not hover else hovertemplate
        )
        for variable in df_plot['variable'].unique():
            df_variable = df_plot[df_plot['variable'] == variable]
            fig.add_trace(
            go.Bar(
                x=df_variable['tech_name'], 
                y=df_variable['value'], 
                marker_color = df_variable['display_color'],
                name=self._glob_cfg['cost_types'][variable]['label'],
                legendgroup=df_variable['display_color'].iloc[0],
                showlegend=not i,
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
        #         name=sector,
        #         showlegend=not i,
        #         hoverinfo='text' if hover else 'skip',
        #         hovertemplate=hovertemplate,
        #         customdata=df_plot[hovercols] if hover else None,
        #         ),
        #     row=1, 
        #     col=i+1
        #     )#, marker_color = df_plot['variable']