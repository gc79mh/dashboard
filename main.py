import dash
from dash import dcc
import dash_bootstrap_components as dbc
from dash import html
import plotly.express as px
import seaborn as sns
from dash.dependencies import Input, Output

app = dash.Dash(__name__)
iris = sns.load_dataset('iris')

app.layout = html.Div(children=[
    html.H1(children='Hello Dash'),
    dcc.Input(value='species', id='in'),
    dcc.Tabs(
        id='tabs',
        value='scatter',
        children=[
            dcc.Tab(label='Scatter', value='scatter'),
            dcc.Tab(label='Histogram', value='hist'),
            dcc.Tab(label='Box', value='box'),
        ]
    ),
    dcc.Graph(
        id='graph',
        # figure will be set by callback
    )
])

@app.callback(
    Output('graph', 'figure'),
    Input('tabs', 'value')
)
def update_graph(tab):
    if tab == 'scatter':
        fig = px.scatter(
            iris, x="sepal_width", y="sepal_length", color="species",
            template="simple_white"
        )
    elif tab == 'hist':
        fig = px.histogram(
            iris, x="sepal_length", color="species",
            template="simple_white"
        )
    elif tab == 'box':
        fig = px.box(
            iris, x="species", y="sepal_length", color="species",
            template="simple_white"
        )
    else:
        fig = {}
    return fig

if __name__ == '__main__':
    app.run(debug=True, port=8050)