from re import template
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
team_ratings = teams[["Team", "Abb", "ORtg", "DRtg",
                      "Conference", "Playoff_status", "W", "L"]]

app.layout = html.Div(children=[
    html.H1(children='NBA Regular Season 21-22'),
    html.P('Visualizing statistics from the 21-22 NBA regular season. Click on a team to show further information about them.', className="sub-header"),
    html.P(['Data for this project is gathered from ',html.A("Basketball-Reference.com.", href="https://www.basketball-reference.com/")], className="sub-header"),
    html.P("Offensive Rating = Points scored per 100 posessions. Defensive Rating = Points allowed per 100 posessions. Net Rating = Offensive Rating - Defensive Rating", className="sub-header"),

    html.Div([
        html.Div([
            dcc.Graph(
                id='team-ratings-graph'
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
            )
        ], className="graphContainer-right")
    ], className="main-container"),


    html.Div([
        html.H2(id='click-data-header', className="team-header"),
        html.Div([
            html.Div([
                html.Img(id='click-data-logo', className="logo"),
                html.P(id='click-data-record')
            ], className="team-container-left"),
            html.Div([
                dcc.Graph(
                    id='team-games-graph'
                )
            ], className="team-container-right")
        ], className="team-container")
    ], id="team-section", style={'display': 'none'})

])


@app.callback(
    Output('team-ratings-graph', 'figure'),
    Input('conference-filter', 'value'),
    Input('playoff-filter', 'value')
)
def update_graph(conference_list, playoff_status_list):
    team_ratings_filtered = team_ratings[team_ratings['Conference'].isin(
        conference_list)]

    team_ratings_filtered = team_ratings_filtered[team_ratings_filtered['Playoff_status'].isin(
        playoff_status_list)]

    ratings_fig = px.scatter(team_ratings_filtered,
                             x="ORtg", y="DRtg", hover_name="Team", custom_data=["Abb"],
                             labels={
                                 "ORtg": "Offensive Rating",
                                 "DRtg": "Defensive Rating"
                             },
                             template='plotly_dark'
                             )

    ratings_fig.update_layout(yaxis_range=[105, 119], xaxis_range=[103, 118])

    ratings_fig.add_shape(type='line',
                          x0=0,
                          y0=avg_team.iloc[0]['DRtg'],
                          x1=1,
                          y1=avg_team.iloc[0]['DRtg'],
                          line=dict(color='#3471eb'),
                          xref='paper',
                          yref='y'
                          )

    ratings_fig.add_shape(type='line',
                          x0=avg_team.iloc[0]['ORtg'],
                          y0=0,
                          x1=avg_team.iloc[0]['ORtg'],
                          y1=1,
                          line=dict(color='#3471eb'),
                          xref='x',
                          yref='paper'
                          )

    for i, row in team_ratings_filtered.iterrows():
        logo_path = row["Abb"]
        team_logo = Image.open(f"./assets/logos/{logo_path.lower()}_logo.png")
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
    Output('click-data-logo', 'src'),
    Output('click-data-record', 'children'),
    Input('team-ratings-graph', 'clickData'))
def display_click_data(clickData):
    if clickData is None:
        header = ""
        visibility = {'display': 'none'}
        fig = {}
        source = ""
        record = ""
    else:
        team_abb = clickData["points"][0]["customdata"][0]

        header = "{} ({})".format(
            clickData["points"][0]["hovertext"], team_abb)
        visibility = {'display': 'block'}

        game_logs = pd.read_csv(f'./data/game_logs/{team_abb.lower()}_log.csv')
        game_logs = game_logs[["G", "ORtg", "DRtg", "W/L", "Opp"]]
        game_logs["NRtg"] = game_logs.apply(
            lambda row: row.ORtg - row.DRtg, axis=1)

        game_logs["NRtgAVG"] = game_logs["NRtg"].cumsum()
        game_logs["NRtgAVG"] = game_logs.apply(
            lambda row: row.NRtgAVG / row.G, axis=1)

        colorsIdx = {'W': 'rgb(4, 189, 17)', 'L': 'rgb(228, 30, 30)'}
        cols = game_logs["W/L"].map(colorsIdx)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=game_logs["G"],
            y=game_logs["NRtgAVG"],
            mode='lines+markers',
            marker=dict(size=10,
                        color=cols),
            customdata=game_logs[["W/L", "Opp", "NRtg"]],
            hovertemplate="<b>Game %{x}</b><br>" +
            "%{customdata[0]} against %{customdata[1]}<br>" +
            "Net Rating for the game=%{customdata[2]:.2f}<br>" +
            "Rolling average of Net Rating=%{y:.2f}<extra></extra>"
        ))
        fig.update_layout(
            title="Rolling Average of the Team's Net Rating Throughout 82 Games",
            xaxis_title="Game",
            yaxis_title="Net Rating",
            template="plotly_dark"
        )

        source = f"/assets/logos/{team_abb.lower()}_logo.png"
        team = team_ratings.loc[team_ratings['Abb'] == team_abb]
        wins = team.iloc[0]['W']
        losses = team.iloc[0]['L']
        record = f"{int(wins)}W - {int(losses)}L"

    return header, fig, visibility, source, record


if __name__ == '__main__':
    app.run_server(debug=True)
