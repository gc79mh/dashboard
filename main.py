import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.express as px
from dash import dash_table
import plotly.express as px
import plotly.graph_objects as go

# Load data
df = pd.read_csv("./owid-covid-data.csv")

# Data cleanup
df['date'] = pd.to_datetime(df['date'])
df = df[~df['location'].isin(['World', 'Asia', 'Africa', 'Europe', 'High-income countries', 'Upper-middle-income countries', 'Lower-middle-income countries', 'Low-income countries', 'North America', 'South America', 'European Union (27)'])]

# Variables
countries = df['location'].unique()
years = sorted(df['date'].dt.year.unique())

# Function that will be used to get correct colors
def get_color_map(selected_countries):
    palette = px.colors.qualitative.Plotly
    return {country: palette[i % len(palette)] for i, country in enumerate(selected_countries)}

app = dash.Dash(__name__)

app.title = "ESSA: COVID-19 Data Dashboard"
app.layout = html.Div([
    html.H2("ESSA: COVID-19 Data Dashboard", style={'textAlign': 'center', 'marginTop': '20px'}),
    dcc.Tabs(id='tabs', value='main', children=[
        # Main tab with features for multiple countries
        dcc.Tab(label='Main', value='main', children=[
            # Main div for this tab
            html.Div([
                # Quick summary section
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

                ], id='quick-summary', style={'margin': '10px 0','fontWeight': 'bold','display': 'flex','alignItems': 'center'}),
                # Display selected countries
                html.Div(id='selected-countries', style={'margin': '10px 0', 'fontWeight': 'bold'}),
                # The main content area
                html.Div([
                    # The left hand side panel with dropdown, search, and checklist
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
                            value=['Poland'],  # Set Poland as default
                            style={'height': '300px', 'overflowY': 'scroll', 'display': 'block'}
                        ),
                    ], style={ 'width': '10%', 'minWidth': '120px', 'maxWidth': '300px', 'marginRight': '30px', 'flexShrink': 0 }),
                    # The 2x2 grid layout for the main content
                    html.Div([
                        # 2x2 grid: left column (line plot, map), right column (leaderboard, data table)
                        html.Div([
                            # Left column
                            html.Div([
                                dcc.Graph(id='main-comparison-line-plot', style={'width': '100%', 'height': '350px'}),
                                dcc.Graph(id='country-map', style={'width': '100%', 'height': '350px', 'marginTop': '20px'})
                            ], style={'flex': 1, 'display': 'flex', 'flexDirection': 'column', 'marginRight': '20px'}),
                            # Right column
                            html.Div([
                                dcc.Graph(id='leaderboard', style={'width': '100%', 'height': '350px'}),
                                html.Div(
                                    id='data-table-container',
                                    style={'height': '350px', 'overflowY': 'auto', 'marginTop': '20px'}
                                )
                            ], style={ 'flex': 1, 'display': 'flex', 'flexDirection': 'column'})
                        ], style={ 'display': 'flex', 'flexDirection': 'row', 'width': '100%' }),
                    ], style={ 'flex': 1, 'display': 'flex', 'flexDirection': 'column', 'overflowX': 'auto' }),
                ], style={'display': 'flex', 'alignItems': 'flex-start', 'height': '100vh'}),
            ])
        ]),
        # The one country overview tab
        dcc.Tab(label='Map Only', value='map', children=[
            html.Div([
                html.Div([
                    dcc.Graph(id='country-map-only', style={'width': '100%', 'height': '350px', 'marginTop': '20px'}),
                ], style={'width': '82vw', 'marginRight': '20px'}),
                html.Div([
                    dcc.Graph(id='country-bar-metrics', style={'width': '100%', 'height': '350px', 'marginTop': '20px'})
                ], style={'width': '40vw'})
            ], style={'display': 'flex', 'flexDirection': 'column', 'alignItems': 'flex-start', 'height': '100vh'})
        ])
    ])
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


@app.callback(
    Output('main-comparison-line-plot', 'figure'),
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

    color_map = get_color_map(selected_countries)

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
    # Filter data for the selected years and selected countries
    dff = df[
        (df['date'].dt.year >= lower) &
        (df['date'].dt.year <= upper) &
        (df['location'].isin(selected_countries))
    ].copy()
    dff['year'] = dff['date'].dt.year
    # Group by country and year, sum all other columns
    agg_columns = ['total_cases', 'total_deaths', 'total_vaccinations', 'population']
    dff_grouped = dff.groupby(['location', 'year'])[agg_columns].sum().reset_index()
    # Reorder columns for display
    dff_grouped = dff_grouped[['location', 'year'] + agg_columns]
    # Sort by selected metric descending
    if selected_metric in dff_grouped.columns:
        dff_grouped = dff_grouped.sort_values(by=selected_metric, ascending=False)
    # Limit rows for performance (optional)
    dff_display = dff_grouped.head(1000)

    # Color mapping for selected countries
    palette = px.colors.qualitative.Plotly
    color_map = {country: palette[i % len(palette)] for i, country in enumerate(selected_countries)}

    style_data_conditional = [
        {
            'if': {'filter_query': f'{{location}} = "{country}"'},
            'color': color_map[country]
        }
        for country in dff_display['location'].unique() if country in color_map
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

@app.callback(
    Output('country-map', 'figure'),
    [Input('country-checklist', 'value'),
     Input('year-slider', 'value'),
     Input('metric-dropdown', 'value')]
)
def update_country_map(selected_countries, year_range, selected_metric):
    lower, upper = year_range
    # Get the latest entry for each country in the range
    dff = df[(df['date'].dt.year >= lower) & (df['date'].dt.year <= upper)].copy()
    dff = dff.sort_values('date').groupby('location').last().reset_index()
    # Ensure iso_code is present
    if 'iso_code' not in dff.columns:
        return go.Figure()
    # Fill color: gradient by selected_metric, gray for missing
    dff['metric_value'] = dff[selected_metric]
    # Border color: palette for selected, transparent for others
    palette = px.colors.qualitative.Plotly
    color_map = {country: palette[i % len(palette)] for i, country in enumerate(selected_countries)}
    dff['border_color'] = dff['location'].map(lambda c: color_map[c] if c in color_map else 'rgba(0,0,0,0)')
    dff['border_width'] = dff['location'].map(lambda c: 3 if c in color_map else 0.5)
    # Fill missing metric with 0 for display
    dff['metric_value'] = dff['metric_value'].fillna(0)
    # Show all countries, but only selected have colored border
    fig = px.choropleth(
        dff,
        locations='iso_code',
        color='metric_value',
        hover_name='location',
        color_continuous_scale='Blues',
        labels={'metric_value': selected_metric.replace('_', ' ').title()},
        projection='natural earth',
        title=f'{selected_metric.replace("_", " ").title()} by Country'
    )
    # Set border color for selected countries
    fig.update_traces(
        marker_line_color=dff['border_color'],
        marker_line_width=dff['border_width'],
        zmin=dff['metric_value'].min(),
        zmax=dff['metric_value'].max()
    )
    fig.update_layout(
        margin={"r":0,"t":30,"l":0,"b":0},
        coloraxis_colorbar=dict(title=selected_metric.replace('_', ' ').title()),
        showlegend=False
    )
    return fig

# Add a new callback for the map-only tab
@app.callback(
    Output('country-map-only', 'figure'),
    [Input('country-checklist', 'value'),
     Input('year-slider', 'value'),
     Input('metric-dropdown', 'value'),
     Input('country-map-only', 'clickData')]
)
def update_country_map_only(selected_countries, year_range, selected_metric, clickData):
    lower, upper = year_range
    dff = df[(df['date'].dt.year >= lower) & (df['date'].dt.year <= upper)].copy()
    dff = dff.sort_values('date').groupby('location').last().reset_index()
    if 'iso_code' not in dff.columns:
        return go.Figure()
    dff['metric_value'] = dff[selected_metric]
    dff['metric_value'] = dff['metric_value'].fillna(0)
    # Determine which country is clicked, default to Poland if none
    selected_iso = None
    if clickData and 'points' in clickData and clickData['points']:
        selected_iso = clickData['points'][0].get('location')
    else:
        # Default to Poland's iso_code if available
        poland_row = dff[dff['location'] == 'Poland']
        if not poland_row.empty:
            selected_iso = poland_row.iloc[0]['iso_code']
    # Set border: red for clicked/default, gray for others
    def border_color(row):
        if selected_iso and row['iso_code'] == selected_iso:
            return 'red'
        return 'rgba(0,0,0,0.5)'
    def border_width(row):
        if selected_iso and row['iso_code'] == selected_iso:
            return 4
        return 0.5
    dff['border_color'] = dff.apply(border_color, axis=1)
    dff['border_width'] = dff.apply(border_width, axis=1)
    fig = px.choropleth(
        dff,
        locations='iso_code',
        color='metric_value',
        hover_name='location',
        color_continuous_scale='Blues',
        labels={'metric_value': selected_metric.replace('_', ' ').title()},
        projection='natural earth',
        title=f'{selected_metric.replace("_", " ").title()} by Country'
    )
    fig.update_traces(
        marker_line_color=dff['border_color'],
        marker_line_width=dff['border_width'],
        zmin=dff['metric_value'].min(),
        zmax=dff['metric_value'].max()
    )
    fig.update_layout(
        margin={"r":0,"t":30,"l":0,"b":0},
        coloraxis_colorbar=dict(title=selected_metric.replace('_', ' ').title()),
        showlegend=False
    )
    return fig

@app.callback(
    Output('country-bar-metrics', 'figure'),
    [Input('country-map-only', 'clickData'),
     Input('year-slider', 'value')]
)
def show_country_metrics_on_map_click(clickData, year_range):
    import plotly.graph_objects as go
    lower, upper = year_range
    if not clickData or 'points' not in clickData or not clickData['points']:
        return go.Figure()
    point = clickData['points'][0]
    iso_code = point.get('location')
    country_row = df[df['iso_code'] == iso_code]
    if country_row.empty:
        return go.Figure()
    country = country_row.iloc[0]['location']
    # Filter for this country and year range
    dff = df[
        (df['location'] == country) &
        (df['date'].dt.year >= lower) &
        (df['date'].dt.year <= upper)
    ].copy()
    if dff.empty:
        return go.Figure()
    dff['year'] = dff['date'].dt.year
    # For each year, get the max value for each metric
    yearly = dff.groupby('year').agg({
        'total_deaths': 'max',
        'total_cases': 'max',
        'total_vaccinations': 'max'
    }).reset_index()
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=yearly['year'], y=yearly['total_deaths'],
        mode='lines+markers', name='Total Deaths', line=dict(color='#EF553B')
    ))
    fig.add_trace(go.Scatter(
        x=yearly['year'], y=yearly['total_cases'],
        mode='lines+markers', name='Total Cases', line=dict(color='#636EFA')
    ))
    fig.add_trace(go.Scatter(
        x=yearly['year'], y=yearly['total_vaccinations'],
        mode='lines+markers', name='Total Vaccinations', line=dict(color='#00CC96')
    ))
    fig.update_layout(
        title=f"{country}: Total Deaths, Cases, Vaccinations by Year",
        yaxis_title="Count",
        xaxis_title="Year",
        template="simple_white"
    )
    return fig

if __name__ == '__main__':
    app.run(debug=True, port=8080)