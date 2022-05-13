from dash import Dash, html, dcc
import plotly.graph_objects as go
import plotly.express as px
from dash.dependencies import Input, Output
import pandas as pd
from PIL import Image

app = Dash(__name__)
server = app.server

df = pd.read_csv("./data/team_stats.csv")
teams = df.iloc[0:30]
avg_team = df.iloc[30:31]
team_ratings = teams[["Team", "Abb", "ORtg", "DRtg", "Logo", "Conference", "Playoff_status"]]

app.layout = html.Div(children=[
    html.H1(children='NBA Regular Season 21-22'),

    html.P('Visualizing statistics from the 21-22 NBA regular season. Click on a team to show further information about them.', className="sub-header"),
    html.P('Below the teams are represented by their offensive and defensive ratings. I.e. Points scored and points allowed per 100 posessions respectively.', className="sub-header"),
    

    html.Div([
        html.Div([
            dcc.Graph(
                id='team-ratings-graph',
                # clickData={'points': [{'hovertext': 'New York Knicks'}]}
            )
        ], className="graphContainer-left"),

        html.Div([
            html.P(['Conference'], className="filter-header"),
            dcc.Checklist(
                ['West', 'East'],
                ['West', 'East'],
                inline=True,
                id='conference-filter',
                labelStyle={'padding': '0.5rem 1.5em 0 0'}
            ),

            html.P('Playoff Status', className="filter-header"),
            dcc.Checklist(
                ['Playoff', 'Lottery'],
                ['Playoff', 'Lottery'],
                inline=True,
                id='playoff-filter',
                labelStyle={'padding': '0.5rem 1.5em 0 0'}
            ),

            # html.P('Division', className="radio-header"),
            # dcc.Dropdown(
            #     ['Atlantic', 'Central', 'Southeast', 'Pacific'],
            #     id='division-filter'
            # )
        ], className="graphContainer-right")
    ], className="main-container"),


    html.Div([
        html.H2(id='click-data-header', className="team-header"),
        dcc.Graph(
            id='team-games-graph'
        )
    ], id="team-section", style={'display': 'none'})

])


@app.callback(
    Output('team-ratings-graph', 'figure'),
    Input('conference-filter', 'value'),
    Input('playoff-filter', 'value')
)
def update_graph(conference_list, playoff_status_list):
    team_ratings_filtered = team_ratings[team_ratings['Conference'].isin(conference_list)]

    team_ratings_filtered = team_ratings_filtered[team_ratings_filtered['Playoff_status'].isin(playoff_status_list)]

    # ratings_fig = go.Figure(
    #     data=go.Scatter(x=team_ratings_filtered["ORtg"],
    #                     y=team_ratings_filtered["DRtg"],
    #                     mode='markers',
    #                     text=team_ratings_filtered["Team"])
    # )

    ratings_fig = px.scatter(team_ratings_filtered,
                             x="ORtg", y="DRtg", hover_name="Team", custom_data=["Abb"])

    ratings_fig.update_layout(yaxis_range=[105, 119], xaxis_range=[103, 118])

    ratings_fig.add_shape(type='line',
                          x0=0,
                          y0=avg_team.iloc[0]['DRtg'],
                          x1=1,
                          y1=avg_team.iloc[0]['DRtg'],
                          line=dict(color='blue'),
                          xref='paper',
                          yref='y'
                          )

    ratings_fig.add_shape(type='line',
                          x0=avg_team.iloc[0]['ORtg'],
                          y0=0,
                          x1=avg_team.iloc[0]['ORtg'],
                          y1=1,
                          line=dict(color='blue'),
                          xref='x',
                          yref='paper'
                          )

    for i, row in team_ratings_filtered.iterrows():
        logo_path = row["Logo"]
        team_logo = Image.open(f"./data/logos/{logo_path}")
        size = 128, 128
        team_logo.thumbnail(size, Image.ANTIALIAS)
        ratings_fig.add_layout_image(
            source=team_logo,
            x=row['ORtg'],
            y=row['DRtg'],
            xref="x",
            yref="y",
            sizex=2.25,
            sizey=2.25,
            xanchor="center",
            yanchor="middle",
        )

    return ratings_fig


@app.callback(
    Output('click-data-header', 'children'),
    Output('team-games-graph', 'figure'),
    Output('team-section', 'style'),
    Input('team-ratings-graph', 'clickData'))
def display_click_data(clickData):
    print(clickData)
    
    if clickData is None:
        header = ""
        visibility = {'display': 'none'}
        fig = {}
    else:
        team_abb = clickData["points"][0]["customdata"][0]
        
        header = "{} ({})".format(clickData["points"][0]["hovertext"], team_abb)
        visibility = {'display': 'block'}
        
        game_logs = pd.read_csv(f'./data/game_logs/{team_abb.lower()}_log.csv')
        game_logs = game_logs[["G", "ORtg", "DRtg", "W/L"]]
        game_logs["NRtg"] = game_logs.apply(lambda row: row.ORtg - row.DRtg, axis=1)
        
        game_logs["NRtgAVG"] = game_logs["NRtg"].cumsum()
        game_logs["NRtgAVG"] = game_logs.apply(lambda row: row.NRtgAVG / row.G, axis=1)
        print(game_logs)
        
        #fig = px.line(game_logs, x="G", y="NRtgAVG", markers=True)
        colorsIdx = {'W': 'rgb(4, 189, 17)', 'L': 'rgb(228, 30, 30)'}
        cols = game_logs["W/L"].map(colorsIdx)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=game_logs["G"],
            y=game_logs["NRtgAVG"],
            mode='lines+markers',
            marker=dict(size=10,
                    color=cols)
        ))
        

    return header, fig, visibility


if __name__ == '__main__':
    app.run_server(debug=True)
