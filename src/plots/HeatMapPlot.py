import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from src.plots.BasePlot import BasePlot
from src.utils import load_yaml_plot_config_file

import numpy as np

class HeatMapPlot(BasePlot):
    figs, cfg = load_yaml_plot_config_file('HeatMapPlot')
    # for now, only one figure so subplots are not needed
    #_add_subfig_name = True

    #def _decorate(...) if required, see Philipps repo

    def plot(self, inputs: dict, outputs: dict, subfig_names: list) -> dict:
        #params = inputs['params']
        df = outputs['heatmap_df']
        contour_df = outputs['contour_df']
        hm_transparency_df = outputs['hm_transparency_df']

        # df = px.data.medals_wide(indexed=True)
        # fig = px.imshow(df)
        fig = go.Figure()


        x_values = df.columns
        y_values = df.index
        z_values = df.values

        custom_cmap = self._make_cmap()
        cmap_labels = ["H2/NH3", "E-Fuel", "Compensation", "CCU", "CCS"]

        fig.add_trace(
            go.Heatmap(
                z=z_values,
                x=x_values,
                y=y_values,
                zmin = 0,
                zmax=1,
                colorscale=custom_cmap,
                colorbar = dict(
                    title=self.cfg['colorbar_title'],
                    tickvals=[0.1, 0.3, 0.5, 0.7, 0.9],
                    ticktext=cmap_labels,
                ),
                hoverinfo="skip",
            )
        )
        fig = self._add_contours(fig, contour_df)

        tr_colorscale = [
            [0.0, "rgba(255, 255, 255, 1.0)"],   # Fully opaque white at value 0
            [1.0, "rgba(255, 255, 255, 0.0)"],   # Fully transparent white at value 100+
        ]

        fig.add_trace(
            go.Heatmap(
                z=hm_transparency_df.values,
                x=hm_transparency_df.columns,
                y=hm_transparency_df.index,
                colorscale=tr_colorscale,
                zmin = 0,
                zmax=100,
                showscale=False,
                hoverinfo="skip",
            )
        )


        fig.update_xaxes(tickfont=dict(size=8))
        fig.update_layout(
        yaxis_title=self.cfg['yaxis_title'],
        xaxis_title=self.cfg['xaxis_title'],
        legend_title='',
        legend=dict(
            yanchor="bottom",
            y=1.15,  # puts legend below the plot
            xanchor="center",
            x=0.5,
            orientation="h"  # makes the legend horizontal
        )
        )

        return {'fig3': fig}

    def _make_cmap(self):
        """Required to make a custom and DISCRETE colormap

        Returns:
            list: list of colors and their associated values
        """
        color_dict_tech = { "h2": "#FCE762",  "efuel": "#FF9446", "comp":"#4C7D5B", "ccu":"#A5A9AF", "ccs":"#3083DC"}
        z_bins = [0, 0.25, 0.5, 0.75, 1]
        colors = [color_dict_tech["h2"], color_dict_tech["efuel"], color_dict_tech["comp"], color_dict_tech["ccu"], color_dict_tech["ccs"]]

        vals = np.r_[np.array(0), np.repeat(list(np.linspace(0, 1, len(z_bins)+1))[1:-1], 2), np.array(1)]
        custom_colorscale = [[j, colors[i//2]] for i, j in enumerate(vals)]
        
        return custom_colorscale

    def _add_contours(self, fig, contour_df):
        #contours
        fig.add_trace(
            go.Contour(
                z=contour_df.values,
                x=contour_df.columns,
                y=contour_df.index,
                contours_coloring='lines',
                colorscale=[
                    [0.0, '#000000'],
                    [1.0, '#000000'],
                ],
                ncontours=5,
                opacity=1,
                contours = dict(
                    showlabels=True,
                ),
                showscale=False,
            )
        )
        return fig
