import os
import json
import random
import numpy as np
import pandas as pd
import dash
from dash import dcc, html
from util import plot_users, plot_network, plot_clusters, plot_closeness

# ----------- FLASK AUTH & ROUTING -----------
from flask import Flask, render_template, request, redirect, session

server = Flask(__name__, 
               template_folder='templates', 
               static_folder='assets', 
               static_url_path='/assets')
server.secret_key = "placeholder_key_for_sample_data"

@server.route("/")
def login_page():
    return render_template("login.html")

@server.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")
    if username and password: 
        session["logged_in"] = True
        return redirect("/dashboard/")
    return render_template("login.html", error="Please enter any username and password")

@server.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# --- DASH INIT ---
app = dash.Dash(
    __name__,
    server=server,
    url_base_pathname='/dashboard/',
    external_stylesheets=['https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap']
)
app.title = 'Network Analysis Dashboard'

@server.before_request
def protect_routes():
    if request.path.startswith("/dashboard") or request.path.startswith("/_dash"):
        if not session.get("logged_in"):
            return redirect("/")

# --- DESIGN SYSTEM ---
COLORS = {
    'background': '#F4F7F9',
    'card': '#FFFFFF',
    'primary': '#4A148C',
    'secondary': '#3B738F',
    'text': '#2D3436',
    'accent': '#6C5CE7',
    'border': '#E0E0E0'
}

CARD_STYLE = {
    'backgroundColor': COLORS['card'],
    'borderRadius': '12px',
    'padding': '25px',
    'boxShadow': '0 4px 12px rgba(0,0,0,0.05)',
    'border': f'1px solid {COLORS["border"]}'
}

# --- LOAD DATA ---
try:
    with open(os.path.join('output', 'cluster1.json')) as f: group1 = json.load(f)
    with open(os.path.join('output', 'cluster2.json')) as f: group2 = json.load(f)
    user_stats = pd.read_csv(os.path.join('output', 'user_stats.csv'), header=0, index_col=0)
    user_stats.columns = [0, 1, 2, 3]
except Exception as e:
    group1 = group2 = {"adjacencym": [[]], "clusters": [], "cluster_names": [], "id_to_name": {}}
    user_stats = pd.DataFrame()

seed = random.randint(1, 100)

# --- TAB RENDER FUNCTION ---
def render_tab(name, res_dict):
    tab_style = {'padding': '15px', 'fontWeight': '600', 'border': 'none', 'backgroundColor': 'transparent', 'color': COLORS['text'], 'cursor': 'pointer'}
    tab_style_selected = {**tab_style, 'borderBottom': f'4px solid {COLORS["primary"]}', 'color': COLORS['primary'], 'backgroundColor': 'rgba(74, 20, 140, 0.05)'}

    return dcc.Tab(label=name, style=tab_style, selected_style=tab_style_selected, children=[
        html.Div(style={'padding': '40px 60px', 'backgroundColor': COLORS['background']}, children=[
            html.Div(style={'display': 'flex', 'gap': '30px', 'width': '100%'}, children=[
                
                # 1. Network Graph Card
                html.Div(style={'flex': '2', **CARD_STYLE}, children=[
                    html.H4('Social Network Visualization', style={'color': COLORS['primary'], 'textAlign': 'center', 'marginTop': '0'}),
                    dcc.Graph(
                        # Modebar removed, zoom/reset functionality remains
                        config={'displayModeBar': False, 'responsive': True},
                        figure=plot_network(np.array(res_dict['adjacencym']), res_dict['clusters'], res_dict['cluster_names'], {int(k): v for k, v in res_dict['id_to_name'].items()}, seed),
                        style={'height': '550px'}
                    ),
                    html.P("💡 Tight clusters represent 'friendship circles.' Nodes sitting between clusters are your 'Bridge' friends.", 
                           style={'fontSize': '0.9em', 'color': '#636e72',  'textAlign': 'center', 'marginTop': '15px'})
                ]),

                # 2. Sidebar Metrics
                html.Div(style={'flex': '1', 'display': 'flex', 'flexDirection': 'column', 'gap': '30px'}, children=[
                    html.Div(style=CARD_STYLE, children=[
                        html.H5('Cluster Path Distribution', style={'color': COLORS['secondary'], 'textAlign': 'center'}),
                        dcc.Graph(
                            config={'displayModeBar': False, 'responsive': True},
                            figure=plot_clusters(res_dict['cluster_size'], res_dict['cluster_max'], res_dict['cluster_min'], res_dict['cluster_avg'], res_dict['cluster_names']),
                            style={'height': '230px'}
                        ),
                        html.P("💡 Shorter vertical lines indicate a 'tight-knit' cluster where members connect directly.", style={'fontSize': '0.85em', 'color': '#636e72', 'marginTop': '10px'})
                    ]),
                    html.Div(style=CARD_STYLE, children=[
                        html.H5('Inter-Cluster Affinity', style={'color': COLORS['secondary'], 'textAlign': 'center'}),
                        dcc.Graph(
                            config={'displayModeBar': False, 'responsive': True},
                            figure=plot_closeness(res_dict['closeness']), 
                            style={'height': '230px'}
                        ),
                        html.P("💡 Darker squares show 'Sister Clusters'—separate groups that share high mutual interaction.", style={'fontSize': '0.85em', 'color': '#636e72', 'marginTop': '10px'})
                    ])
                ])
            ])
        ])
    ])

# --- MAIN LAYOUT ---
app.layout = html.Div(style={'fontFamily': 'Inter, sans-serif', 'backgroundColor': COLORS['background'], 'minHeight': '100vh'}, children=[
    
    # Unified Header
    html.Div(style={
        'backgroundColor': COLORS['primary'],
        'padding': '30px 60px',
        'display': 'flex',
        'alignItems': 'center',
        'boxShadow': '0 4px 10px rgba(0,0,0,0.1)'
    }, children=[
        html.Img(src='/assets/network.png', style={'height': '80px', 'marginRight': '20px'}),
        html.Div(style={'flex': '1'}, children=[
            html.H1('Network Analysis Dashboard', style={'color': 'white', 'margin': '0', 'fontSize': '2em'}),
            html.P('Interactive Visual Insights into Social Connectivity', style={'color': 'rgba(255,255,255,0.7)', 'margin': '0'})
        ]),
        html.A("Logout", href="/logout", style={'color': 'white', 'background': COLORS['accent'], 'padding': '10px 20px', 'borderRadius': '8px', 'textDecoration': 'none', 'fontWeight': '600'})
    ]),

    # 🔍 Expanded Analytics Guide & Tips Section
    html.Div(style={'display': 'flex', 'padding': '40px 60px', 'gap': '30px'}, children=[
        html.Div(style={'flex': '1', **CARD_STYLE}, children=[
            html.H4('🔍 Analytics Guide & Tips', style={'color': COLORS['primary'], 'marginTop': '0', 'borderBottom': f'1px solid {COLORS["border"]}', 'paddingBottom': '10px'}),
            html.Div(style={'fontSize': '0.95em', 'lineHeight': '1.6'}, children=[
                html.B("Community Detection", style={'color': COLORS['accent']}),
                html.P("Nodes of the same color belong to a cluster, representing people mathematically grouped by shared connections."),
                
                html.B("Proximity & Influence", style={'color': COLORS['accent']}),
                html.P("The closer two nodes are, the higher their 'Closeness Centrality'. Nodes at the edges are typically peripheral connections."),
                
                html.B("Identifying 'Bridges'", style={'color': COLORS['accent']}),
                html.P("Nodes positioned between different colored clusters are 'bridge friends' connecting separate social groups."),

                html.B("Interactive Tips", style={'color': COLORS['accent']}),
                html.Ul([
                    html.Li("Hover over any node to reveal masked identities."),
                    html.Li("Click and drag to zoom into dense population areas."),
                    html.Li("Double-click any graph to reset the view to original scale."),
                    html.Li("Click cluster names in the legend to isolate specific circles.")
                ])
            ])
        ]),

        # Global Stats Card
        html.Div(style={'flex': '1.5', **CARD_STYLE}, children=[
            html.H5('📈 Mutual Connection Distribution', style={'textAlign': 'center', 'color': COLORS['secondary'], 'marginTop': '0'}),
            dcc.Graph(
                config={'displayModeBar': False, 'responsive': True},
                figure=plot_users(user_stats),
                style={'height': '320px'}
            ),
            html.P("💡 A higher blue line percentage indicates a deeper integration into your social circle.", 
                   style={'textAlign': 'center', 'fontSize': '0.9em', 'color': '#636e72', 'marginTop': '15px'})
        ])
    ]),

    # Tabs Section
    html.Div(style={'padding': '0 60px 40px 60px'}, children=[
        dcc.Tabs(children=[
            render_tab('Community View (8 Clusters)', group1),
            render_tab('Granular View (16 Clusters)', group2)
        ], style={'borderBottom': f'1px solid {COLORS["border"]}'})
    ])
])

if __name__ == '__main__':
    server.run(debug=True)