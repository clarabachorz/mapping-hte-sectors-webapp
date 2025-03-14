import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from src.plots.BasePlot import BasePlot
from src.utils import load_yaml_plot_config_file


class AbatementCostPlot(BasePlot):
    figs, cfg = load_yaml_plot_config_file('AbatementCostPlot')
    _add_subfig_name = True

    sectors = [ "chem", "plane","ship", "steel", "cement"]

    def plot(self, inputs: dict, outputs: dict, subfig_names: list) -> dict:
        tech_displayname = pd.Series(outputs['full_df']["code"].values, index = outputs['full_df']["tech"]).to_dict()

        df = outputs['full_df']

        #df = df[df.index.to_series().str.contains('|'.join(self.sectors))].reset_index()
        df[["type", "sector"]] = df["tech"].str.split("_", expand=True)
        df = df.drop(df[df['tech']=='h2_plane'].index)

        #filter out fossil rows and fuel rows
        df = df[(df['sector'].isin(self.sectors))&(~df['fscp'].isnull())]
        
        subplot_titles = [self._glob_cfg['sector'][sector]['label'] for sector in self.sectors]
        fig = make_subplots(rows=1, cols=5, 
                            subplot_titles=subplot_titles)

        for i,sector in enumerate(self.sectors):
            df_plot = self._prepare(df, sector)

            df_plot['tech_name'] = df_plot['tech'].map(tech_displayname)
            self._add_bars(fig, i, sector, df_plot)

        fig.update_layout(
        barmode='stack',
        yaxis_title=self.cfg['yaxis_title'],
        margin=dict(l=0, r=0, t=50, b=250),
        )

        return {'fig3': fig}
    
    
    def _prepare(self, df: pd.DataFrame, sector: str) -> pd.DataFrame:

        #filter to get the correct sector
        df_plot = df[df["sector"]==sector]

        if self._target == 'webapp':
            df_plot['hover_ptype'] = df_plot['code']

            df_plot['display_color'] = df_plot['type'].map({
                var: display['colour']
                for var, display in self._glob_cfg['abatement_types'].items()
            })

            df_plot['type_label'] = df_plot['type'].map({
                var: display['label']
                for var, display in self._glob_cfg['abatement_types'].items()
            })
            df_plot['unit'] = "EUR/tCO2"

        return df_plot

    def _add_bars(self, fig, i, sector, df_plot):

        # hover = self._target == 'webapp'
        hover = True
        hovercols = ['hover_ptype','type_label', 'fscp', 'unit'] if hover else None
        hovercomp = {
            'header_basic': '<b>%{customdata[0]}</b><br>',
            'type': 'Abatement option type: %{customdata[1]}<br>',
            'cost':'Abatement cost: %{customdata[2]:.2f} %{customdata[3]}'
        }
        hovertemplate = ''.join(hovercomp[c] for c in ['header_basic','type', 'cost'])

        hovertemplate = (
            None if not hover else hovertemplate
        )

        fig.add_trace(
        go.Bar(
            x=df_plot['code'], 
            y=df_plot['fscp'], 
            marker_color = df_plot['display_color'],
            name = "",
            showlegend=False,
            hoverinfo='skip',
            hovertemplate=hovertemplate,
            customdata=df_plot[hovercols].values.tolist() if hover else None,
            ),
        row=1, 
        col=i+1
        )