import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go


def showDataFrame(data):
    tab = dash_table.DataTable(
                id='table',
                columns=[{"name": i, "id": i} for i in data.columns],
                data=data.to_dict('records'),
                page_action = 'native',
                page_current = 0,
                page_size = 10
            )

    return tab

def showBarGraph(data):
    tab = dcc.Graph(
                id='example-graph',
                figure={
                'data': [
                    {'x': data['Generation'], 'y': data['Attack'], 'type': 'bar', 'name': 'Attack'},
                    {'x': data['Generation'], 'y': data['Speed'], 'type': 'bar', 'name': 'Speed'},
                ],
                'layout': {'title': 'Dashboard Pokemon Attack', 'barmode' : 'stack'}
            }
            )
    return tab