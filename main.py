import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.express as px
from dash import dash_table

# Load data
df = pd.read_csv("./owid-covid-data.csv")
df['date'] = pd.to_datetime(df['date'])
df = df[~df['location'].isin(['World', 'Asia', 'Africa', 'Europe', 'High-income countries', 'Upper-middle-income countries', 'Lower-middle-income countries', 'Low-income countries', 'North America', 'South America', 'European Union (27)'])]
# Get list of countries
countries = df['location'].unique()

years = sorted(df['date'].dt.year.unique())


def get_color_map(selected_countries):
    palette = px.colors.qualitative.Plotly
    return {country: palette[i % len(palette)] for i, country in enumerate(selected_countries)}

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H2("ESSA: COVID-19 Data Dashboard", style={'textAlign': 'center', 'marginTop': '20px'}),
    html.Div([
        html.Div(
            dcc.RangeSlider(
                id='year-slider',
                min=years[0],
                max=years[-1],
                value=[2020, 2024],
                marks={str(y): str(y) for y in years},
                step=1,
                allowCross=False,
                tooltip={"placement": "bottom", "always_visible": True},
                pushable=1
            ),
            style={'width': '250px', 'padding': '10px', 'border': '1px solid #ccc', 'borderRadius': '5px', 'marginRight': '10px'}
        ),
        html.Div(id='summary-vacc', style={'padding': '10px', 'border': '1px solid #ccc', 'borderRadius': '5px', 'marginRight': '10px'}),
        html.Div(id='summary-cases', style={'padding': '10px', 'border': '1px solid #ccc', 'borderRadius': '5px', 'marginRight': '10px'}),
        html.Div(id='summary-deaths', style={'padding': '10px', 'border': '1px solid #ccc', 'borderRadius': '5px'})
    ], id='quick-summary', style={
        'margin': '10px 0',
        'fontWeight': 'bold',
        'display': 'flex',
        'alignItems': 'center'
    }),
    html.Div(id='selected-countries', style={'margin': '10px 0', 'fontWeight': 'bold'}),
    html.Div([
        html.Div([
            dcc.Dropdown(
                id='metric-dropdown',
                options=[
                    {'label': 'Total Deaths', 'value': 'total_deaths'},
                    {'label': 'Total Cases', 'value': 'total_cases'},
                    {'label': 'Total Vaccinations', 'value': 'total_vaccinations'}
                ],
                value='total_deaths',
                clearable=False,
                style={'marginBottom': '10px'}
            ),
            dcc.Input(
                id='country-search',
                type='text',
                placeholder='Search country...',
                style={'width': '100%', 'marginBottom': '10px'}
            ),
            dcc.Checklist(
                id='country-checklist',
                options=[{'label': c, 'value': c} for c in countries],
                value=['Poland'],
                style={'height': '300px', 'overflowY': 'scroll', 'display': 'block'}
            ),
        ], style={
            'width': '10%',
            'minWidth': '120px',
            'maxWidth': '300px',
            'marginRight': '30px',
            'flexShrink': 0
        }),
        html.Div([
            dcc.Graph(id='line-plot', style={'width': '100%', 'height': '350px'}),
            dcc.Graph(id='leaderboard', style={'width': '100%', 'height': '350px'})
        ], style={
            'flex': 1,
            'display': 'flex',
            'flexDirection': 'row',
            'overflowX': 'auto'
        }),
    ], style={'display': 'flex', 'alignItems': 'flex-start', 'height': '100vh'}),
    html.Div(id='data-table-container', style={'marginTop': '30px'})

])

@app.callback(
    Output('country-checklist', 'options'),
    Input('country-search', 'value')
)
def update_checklist_options(search_value):
    if not search_value:
        filtered = countries
    else:
        filtered = [c for c in countries if search_value.lower() in c.lower()]
    return [{'label': c, 'value': c} for c in filtered]

import plotly.express as px
import plotly.graph_objects as go

# ...existing code...
@app.callback(
    Output('line-plot', 'figure'),
    [Input('country-checklist', 'value'),
     Input('metric-dropdown', 'value'),
     Input('year-slider', 'value')]
)
def update_line_plot(selected_countries, selected_metric, year_range):
    lower, upper = year_range
    dff = df[
        df['location'].isin(selected_countries) &
        (df['date'].dt.year >= lower) &
        (df['date'].dt.year <= upper)
    ].copy()
    dff['year'] = dff['date'].dt.year
    metric_by_year = dff.groupby(['location', 'year'])[selected_metric].max().reset_index()

    # Color mapping for consistency
    palette = px.colors.qualitative.Plotly
    color_map = {country: palette[i % len(palette)] for i, country in enumerate(selected_countries)}

    # Average for ALL countries (in the selected year range)
    df_all = df[(df['date'].dt.year >= lower) & (df['date'].dt.year <= upper)].copy()
    df_all['year'] = df_all['date'].dt.year
    metric_all = df_all.groupby(['location', 'year'])[selected_metric].max().reset_index()
    avg_by_year = metric_all.groupby('year')[selected_metric].mean().reset_index()

    fig = px.line(
        metric_by_year,
        x='year',
        y=selected_metric,
        color='location',
        markers=True,
        color_discrete_map=color_map,
        # title=f'COVID-19 {selected_metric.replace("_", " ").title()} by Year',
        title='',
        labels={selected_metric: selected_metric.replace("_", " ").title(), 'year': 'Year', 'location': 'Country'},
        template="simple_white"
    )
    # Add average line (all countries)
    fig.add_trace(
        go.Scatter(
            x=avg_by_year['year'],
            y=avg_by_year[selected_metric],
            mode='lines+markers',
            name='Average (All Countries)',
            line=dict(color='black', width=3, dash='dash')
        )
    )
    fig.update_layout(
        showlegend=False,
        xaxis_title=None,
        yaxis_title=None
    )
    return fig

@app.callback(
    Output('leaderboard', 'figure'),
    [Input('country-checklist', 'value'),
     Input('metric-dropdown', 'value'),
     Input('year-slider', 'value')]
)
def update_leaderboard(selected_countries, selected_metric, year_range):
    lower, upper = year_range
    # Filter for the selected year range
    dff = df[(df['date'].dt.year >= lower) & (df['date'].dt.year <= upper)].copy()
    # Aggregate the metric for each country in the selected range (use max or sum as appropriate)
    agg_metric = dff.groupby('location')[selected_metric].max().reset_index()
    # Get top 10 by metric
    top10 = agg_metric.nlargest(10, selected_metric)
    # Ensure all selected countries are included
    selected_df = agg_metric[agg_metric['location'].isin(selected_countries)]
    # Combine and drop duplicates, keeping order: selected first, then top10
    combined = pd.concat([selected_df, top10]).drop_duplicates(subset=['location'])
    # Sort: selected countries first, then by metric
    combined['is_selected'] = combined['location'].isin(selected_countries)
    combined = combined.sort_values(['is_selected', selected_metric], ascending=[False, False]).head(10)
    combined = combined.drop(columns='is_selected')
    # Color mapping: selected countries get palette, others get black
    palette = px.colors.qualitative.Plotly
    color_map = {}
    for i, country in enumerate(combined['location']):
        if country in selected_countries:
            color_map[country] = palette[selected_countries.index(country) % len(palette)]
        else:
            color_map[country] = 'black'
    fig = px.bar(
        combined,
        x=selected_metric,
        y='location',
        orientation='h',
        color='location',
        color_discrete_map=color_map,
        # title=f'Leaderboard: {selected_metric.replace("_", " ").title()} ({lower}-{upper})',
        title='',
        labels={selected_metric: selected_metric.replace("_", " ").title(), 'location': 'Country'},
        template="simple_white"
    )
    fig.update_layout(yaxis={'categoryorder':'total ascending'}, height=400, showlegend=False, yaxis_title=None)
    return fig


@app.callback(
    Output('selected-countries', 'children'),
    Input('country-checklist', 'value')
)
def show_selected_countries(selected):
    if not selected:
        return "No countries selected."
    color_map = get_color_map(selected)
    return [
        html.Span(
            country,
            style={'color': color_map[country], 'fontWeight': 'bold', 'marginRight': '10px'}
        )
        for country in selected
    ]

@app.callback(
    [Output('summary-vacc', 'children'),
     Output('summary-cases', 'children'),
     Output('summary-deaths', 'children')],
    [Input('country-checklist', 'value'),
     Input('year-slider', 'value')]
)
def update_summary(selected_countries, year_range):
    if not selected_countries or not year_range:
        return "Vaccinations: N/A", "Confirmed Cases: N/A", "Confirmed Deaths: N/A"
    lower, upper = year_range
    dff = df[df['location'].isin(selected_countries) & (df['date'].dt.year >= lower) & (df['date'].dt.year <= upper)]
    if dff.empty:
        return "Vaccinations: N/A", "Confirmed Cases: N/A", "Confirmed Deaths: N/A"
    latest = dff.sort_values('date').groupby('location').last().reset_index()
    total_pop = latest['population'].sum() if 'population' in latest else None
    total_vacc = latest['total_vaccinations'].sum() if 'total_vaccinations' in latest else None
    total_cases = latest['total_cases'].sum() if 'total_cases' in latest else None
    total_deaths = latest['total_deaths'].sum() if 'total_deaths' in latest else None

    vacc_pct = f"{(total_vacc / total_pop * 100):.2f}%" if total_pop and total_vacc else "N/A"
    cases_pct = f"{(total_cases / total_pop * 100):.2f}%" if total_pop and total_cases else "N/A"
    deaths_pct = f"{(total_deaths / total_pop * 100):.2f}%" if total_pop and total_deaths else "N/A"

    return (
        f"Vaccinations: {vacc_pct}",
        f"Confirmed Cases: {cases_pct}",
        f"Confirmed Deaths: {deaths_pct}"
    )

@app.callback(
    Output('data-table-container', 'children'),
    [Input('country-checklist', 'value'),
     Input('year-slider', 'value'),
     Input('metric-dropdown', 'value')]
)
def update_table(selected_countries, year_range, selected_metric):
    lower, upper = year_range
    # Filter data for the selected years
    dff = df[(df['date'].dt.year >= lower) & (df['date'].dt.year <= upper)].copy()
    # Show only relevant columns for clarity
    columns = ['location', 'date', 'total_cases', 'total_deaths', 'total_vaccinations', 'population']
    dff = dff[columns]
    # Limit rows for performance (optional)
    dff = dff.sort_values(['location', 'date'])
    dff_display = dff.head(1000)  # or remove .head(1000) for all rows

    # Color mapping for selected countries
    palette = px.colors.qualitative.Plotly
    color_map = {country: palette[i % len(palette)] for i, country in enumerate(selected_countries)}

    style_data_conditional = [
        {
            'if': {'filter_query': f'{{location}} = "{country}"'},
            'backgroundColor': color_map[country],
            'color': 'white' if color_map[country] != '#FFD700' else 'black'  # for yellow, use black text
        }
        for country in selected_countries if country in color_map
    ]

    return dash_table.DataTable(
        columns=[{"name": i.replace('_', ' ').title(), "id": i} for i in dff_display.columns],
        data=dff_display.to_dict('records'),
        page_size=20,
        style_data_conditional=style_data_conditional,
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left', 'minWidth': '100px', 'maxWidth': '200px', 'whiteSpace': 'normal'},
        style_header={'fontWeight': 'bold', 'backgroundColor': '#f9f9f9'}
    )

if __name__ == '__main__':
    app.run(debug=True, port=8080)