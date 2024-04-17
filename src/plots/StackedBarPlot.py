import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from src.plots.BasePlot import BasePlot
from src.utils import load_yaml_plot_config_file


class StackedBarPlot(BasePlot):
    figs, cfg = load_yaml_plot_config_file('StackedBarPlot')
    _add_subfig_name = True

    sectors = ["ship", "steel", "plane", "chem", "cement"]

    def plot(self, inputs: dict, outputs: dict, subfig_names: list) -> dict:
        tech_displayname = pd.Series(outputs['full_df']["code"].values, index = outputs['full_df']["tech"]).to_dict()

        df = outputs['full_df_breakdown']

        df = df[df.index.to_series().str.contains('|'.join(self.sectors))].reset_index()
        df[["type", "sector"]] = df["tech"].str.split("_", expand=True)
        df = df.drop(df[df['tech']=='h2_plane'].index)
        

        fig = make_subplots(rows=1, cols=5, 
                            subplot_titles=self.sectors)

        for i,sector in enumerate(self.sectors):
            df_plot = self._prepare(df, sector)

            df_plot['tech_name'] = df_plot['tech'].map(tech_displayname)
            self._add_bars(fig, i, sector, df_plot)
            # fig.add_trace(go.Bar(x=df_plot['tech'], y=df_plot['value'], name=df_plot['variable']), row=1, col=i+1)#, marker_color = df_plot['variable']
            

        # # some styling
        # fig.update_layout(
        #     xaxis_title=self.cfg['xaxis_title'],
        #     yaxis_title=self.cfg['yaxis_title'],
        # )

        return {'fig2': fig}
    
    def _prepare(self, df: pd.DataFrame, sector: str) -> pd.DataFrame:

        #filter to get the correct sector, and put df in long format
        df_plot = df[df["sector"]==sector]
        df_plot = df_plot.drop(columns=['LCO', 'type', 'sector']).melt(id_vars='tech').fillna(0.0)

        #print(self._glob_cfg['sector_names'].items())
        #continue here later, use to get hoover data

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

        fig.add_trace(
            go.Bar(
                x=df_plot['tech_name'], 
                y=df_plot['value'], 
                marker_color = df_plot['display_color'],
                name=sector,
                showlegend=not i,
                hoverinfo='text' if hover else 'skip',
                hovertemplate=hovertemplate,
                customdata=df_plot[hovercols] if hover else None,
                ),
            row=1, 
            col=i+1
            )#, marker_color = df_plot['variable']