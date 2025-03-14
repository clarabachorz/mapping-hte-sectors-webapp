import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from src.plots.BasePlot import BasePlot
from src.utils import load_yaml_plot_config_file

import numpy as np

class HeatMapPlot(BasePlot):
    figs, cfg = load_yaml_plot_config_file('HeatMapPlot')

    def plot(self, inputs: dict, outputs: dict, subfig_names: list) -> dict:

        df = outputs['heatmap_df']
        contour_df = outputs['contour_df']
        hm_transparency_df = outputs['hm_transparency_df']
        optioninfo_df = outputs['optioninfo_df']

        case_label = self._glob_cfg['case'][inputs['selected_case']]['label']

        #get unique sectors
        unique_sectors = ["chem", "plane", "ship", "steel", "cement"]

        #create subplot
        cols = len(unique_sectors)
        fig = make_subplots(rows=1, cols=cols, 
                            x_title=self.cfg['xaxis_title'],
                            subplot_titles=[f"{self._glob_cfg['sector'][sector]['label']}" for sector in unique_sectors])


        #fig = go.Figure()
        custom_cmap = self._make_cmap()
        cmap_labels = ["H2/NH3", "Synfuel", "Compensation", "CCU", "CCS"]

        for i, sector in enumerate(unique_sectors, start=1):

            #extract the sector data
            sector_df = df.xs(sector, level="sector")
            sector_contour_df = contour_df.xs(sector, level="sector")
            sector_transparency_df = hm_transparency_df.xs(sector, level="sector")
            sector_optioninfo_df = optioninfo_df.xs(sector, level="sector")

            x_values = sector_df.columns
            y_values = sector_df.index
            z_values = sector_df.values



            fig.add_trace(
                go.Heatmap(
                    z=z_values,
                    x=x_values,
                    y=y_values,
                    zmin = 0,
                    zmax=1,
                    colorscale=custom_cmap,
                    showscale=(i == cols),
                    colorbar = dict(
                        title=self.cfg['colorbar_title'],
                        tickvals=[0.1, 0.3, 0.5, 0.7, 0.9],
                        ticktext=cmap_labels,
                        x = 0.5,
                        y= -0.45,
                        orientation='h'
                    ) if i == cols else None,
                    hoverinfo="skip",
                ),
                row = 1, col = i
            )
            fig = self._add_contours(fig, sector_contour_df, z_values=sector_optioninfo_df.values, row = 1, col = i)

            tr_colorscale = [
                [0.0, "rgba(250, 250, 250, 1.0)"],
                [1.0, "rgba(250, 250, 250, 0.0)"],
            ]

            fig.add_trace(
                go.Heatmap(
                    z=sector_transparency_df.values,
                    x=sector_transparency_df.columns,
                    y=sector_transparency_df.index,
                    colorscale=tr_colorscale,
                    zmin = 0,
                    zmax=100,
                    showscale=False,
                    hoverinfo="skip",
                ),
                row= 1, col = i
            )

            if i > 1:
                fig.update_yaxes(showticklabels=False, row=1, col=i)
                

        fig.update_xaxes(tickfont=dict(size=8))
        fig.update_layout(
        margin=dict(l=50, r=10, t=100, b=50),
        title=self.cfg['title']+case_label,
        yaxis_title=self.cfg['yaxis_title'],
        #xaxis_title=self.cfg['xaxis_title'],
        legend_title='',
        legend=dict(
            yanchor="bottom",
            y=1.15,  # puts legend below the plot
            xanchor="center",
            x=0.5,
            orientation="h"  # makes the legend horizontal
        )
        )

        return {'fig4': fig}

    def _make_cmap(self):
        """Required to make a custom and DISCRETE colormap

        Returns:
            list: list of colors and their associated values
        """
        color_dict_tech = {"h2": "#FCE762",  "efuel": "#FF9446", "comp":"#4C7D5B", "ccu":"#A5A9AF", "ccs":"#3083DC"}
        z_bins = [0, 0.25, 0.5, 0.75, 1]
        colors = [color_dict_tech["h2"], color_dict_tech["efuel"], color_dict_tech["comp"], color_dict_tech["ccu"], color_dict_tech["ccs"]]

        vals = np.r_[np.array(0), np.repeat(list(np.linspace(0, 1, len(z_bins)+1))[1:-1], 2), np.array(1)]
        custom_colorscale = [[j, colors[i//2]] for i, j in enumerate(vals)]
        
        return custom_colorscale

    def _add_contours(self, fig, contour_df, z_values, row, col):
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
                hoverinfo="text",
                hovertemplate="<b>Non-fossil CO<sub>2</sub> cost:</b>: €%{x}/tCO<sub>2</sub><br>"
                      "<b>Low-emission H<sub>2</sub> cost</b>: €%{y}/MWh<br>"
                      #"<b>Abatement cost</b>: €%{z:.2f}/tCO2<extra></extra>"
                      "<b>Abatement cost</b>: €%{z:.2f}/tCO2<br>"
                      "<b>Abatement option</b>: %{customdata}<extra></extra>",
                customdata=z_values,
            ),
            row = row, col = col
        )
        return fig
