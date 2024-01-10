import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from src.plots.BasePlot import BasePlot
from src.utils import load_yaml_plot_config_file


class StackedBarPlot(BasePlot):
    figs, cfg = load_yaml_plot_config_file('StackedBarPlot')
    _add_subfig_name = True

    def plot(self, inputs: dict, outputs: dict, subfig_names: list) -> dict:
        df = outputs['df']

        df_plot = df.drop(columns='LCO').melt(id_vars='tech').fillna(0.0)

        # create figure
        fig = px.bar(df_plot, x='tech', y='value', color='variable')

        # some styling
        fig.update_layout(
            xaxis_title=self.cfg['xaxis_title'],
            yaxis_title=self.cfg['yaxis_title'],
        )

        return {'fig1': fig}
