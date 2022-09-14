# Visualization of Step Count Raw Data along with time
import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
from plotly.subplots import make_subplots


import os
import pandas as pd
import datetime as dt

app = dash.Dash(__name__,url_base_pathname = "/carryingwearing/")
server = app.server
cwd = os.getcwd()
user_dir = os.path.join(cwd, "Data", "Minute")
users = sorted([file.split(".csv")[0] for file in os.listdir(user_dir)])

color = {'PHONE': '#1f77b4', 'WEARABLE': '#ff7f0e'}


def getPlotlyGraph(uid, date):
    udf = pd.read_csv(os.path.join(
        user_dir, f"{uid}.csv"), header=0, index_col=None)
    udf.loc[:, "READABLE_START"] = pd.to_datetime(udf["READABLE_START"])
    date = dt.datetime.strptime(date, '%Y-%m-%d').date()
    if date < udf.iloc[0, 2].date():
        date = udf.iloc[0, 2].date()
    elif date > udf.iloc[-1, 2].date():
        date = udf.iloc[-1, 2].date()

    fig = make_subplots(rows=2, cols=1, specs=[[{}], [{}]],
                        shared_xaxes=True, shared_yaxes=True,
                        horizontal_spacing=0, vertical_spacing=0)
    for idx, device in enumerate(color.keys()):
        fig.append_trace(
            go.Bar(
                x=udf["READABLE_START"],
                y=udf[device + "_STEP"].values * (1-2*idx),
                orientation='v',
                showlegend=True,
                name=device,
                hovertemplate="%{y}",
                marker=dict(
                    color=color[device]
                )),
            row=idx+1, col=1)
    fig.update_yaxes(fixedrange=True, range=[0, 200], row=1, col=1)
    fig.update_yaxes(fixedrange=True, range=[-200, 0], row=2, col=1)
    fig.update_xaxes(
        range=[date, date + dt.timedelta(days=1)],
    )
    fig.update_layout(
        yaxis=dict(
            tickmode='array',
            tickvals=[0, 100, 200],
            ticktext=[0, 100, 200],
            title=list(color.keys())[0]
        ),
        yaxis2=dict(
            tickmode='array',
            tickvals=[0, -100, -200],
            ticktext=[0, 100, 200],
            title=list(color.keys())[1]
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=.5,
            font=dict(
                size=18,
            ),
        ),
        font=dict(
            size=18,
        ),
    )
    return fig, date


app.layout = html.Div(children=[
    html.Div(
        children=[
            dcc.Dropdown(
                id='uid',
                options=[{'label': i, 'value': i} for i in users],
                value=users[0],
                style={
                    'width': '150px',
                }
            ),
            dcc.DatePickerSingle(
                id='date',
                min_date_allowed=dt.date(2021, 1, 1),
                max_date_allowed=dt.date(2022, 12, 31),
                initial_visible_month=dt.date(2021, 1, 1),
                date=dt.date(2021, 1, 1)
            ),
        ],
        style={
            'display': 'flex',
            'flex-direction': 'row',
            'gap': '15px',
            'align-items': 'center',
            'justify-content': 'center'
        }
    ),
    dcc.Graph(
        id='graph',
    )
], style={
    'padding': '20px',
})


@app.callback(
    [Output("graph", "figure"),
     Output('date', 'date')],
    Input("uid", "value"),
    Input('date', 'date')
)
def cb_render(uid, date):
    graph, date = getPlotlyGraph(uid, date)
    return graph, date


if __name__ == '__main__':
    app.run_server(debug=True)
