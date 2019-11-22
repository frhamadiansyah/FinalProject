import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go
from dash.dependencies import Input, Output, State
import datetime
from src.tweetScrape import append_db
import pickle
from src.text_process import text_process, loadModel
from sqlalchemy import create_engine
from PIL import Image
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
import matplotlib.pyplot as plt
import nltk
import re


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWlwgP.css']

app = dash.Dash(__name__, external_stylesheets = external_stylesheets)

def word_extract(x):
    hashtags = []
    # Loop over the words in the tweet
    for i in x:
        ht = re.findall(r"(\w+)", i)
        for j in ht:
          hashtags.append(j)

    return hashtags



timeInterval = 90


app.layout = html.Div(children=[
    html.H1('Twitter Sentiment Dashboard', style = {'text-align' : 'center','padding' : '25px'}),
    html.P('Created by Fandri', style = {'text-align' : 'center'}),

    ## Add tab
    dcc.Tabs(value = 'tabs', id = 'tabs-1',children = [
        dcc.Tab(label= 'Twitter Dataset', value = 'tab-nol', children = [
            ## Add graph
            html.Div([
                html.P('Please input keyword : '),
                html.Div([
                    
                    html.Div(dcc.Input(id='search-tweet-bar', value='jokowi', type='text'),className = 'col-3', style = {'margin-top' : '25px', 'margin-bottom' : '25px'}),
                    html.Div(html.Button('Search', id = 'search-tweet'), className = 'col-3', style = {'margin-top' : '25px', 'margin-bottom' : '25px'}),
                ], className = 'row'),
                html.Div(children = html.H2("This Dashboard Shows Tweet's Containing"), style = {'text-align' : 'center'}),
                html.Div(id='search-keyword', children = 'jokowi', style = {'text-align' : 'center'}),
                html.Div(id='live-update-graph',className = 'col-12', style = {'margin-top' : '25px', 'margin-bottom' : '25px'}),
                html.Div(id='live-update-table', style = {'margin-top' : '25px', 'margin-bottom' : '25px'},className = 'col-12'),
                # html.H4('The time is: ' + str(datetime.datetime.now())),
                
                html.Div(id='live-update-influencer',className = 'col-12', style = {'margin-top' : '25px', 'margin-bottom' : '25px'}),
                

                html.Div([
                    html.Div(id = 'positive-graph', className = 'col-6'),
                    html.Div(id = 'negative-graph', className = 'col-6'),
                ], className = 'row'),

                dcc.Interval(
                id='interval-component',
                interval=timeInterval*1000, # in milliseconds
                n_intervals=0)
            ])
        ]
        ),
        # dcc.Tab(label= 'Train data Visualize', value = 'tab-satu', children = [
        #     ## Add graph
            
        # ]
        # ),
        dcc.Tab(label= 'Check your Tweets!', value = 'tab-dua', children = [
            ## Add graph
            ## Add input bar
            html.Div(html.P('Check your Tweet!')), 
            html.Div(dcc.Input(id='tweet-bar', value='masukkan string', type='text'),className = 'col-6', style = {'align':'center','margin-top' : '25px', 'margin-bottom' : '25px'}),

            ## Add search button
            html.Div(html.Button('Check!', id = 'check-tweet'), className = 'col-6', style = {'align':'center','margin-top' : '25px', 'margin-bottom' : '25px'}),

            html.Div(id = 'result-sentimen', children = [
                html.H4(' :)')
            ],style = {'align':'center','margin-top' : '25px', 'margin-bottom' : '25px'})

            
        ]
        ),
        dcc.Tab(label= 'References', value = 'tab-tiga', children = [
            ## Add graph
            html.H4('List of reference:'),
            html.Ul([html.Li('dataset using dataset from github user @riochr17 for his final project (https://github.com/riochr17/Analisis-Sentimen-ID.git)'),
                    html.Li('Indonesian Slang word dataset from github user @nasalsabila (https://github.com/nasalsabila/kamus-alay.git) and paper titled "Ibrohim, M.O., Budi, I.. A Dataset and Preliminaries Study for Abusive Language Detection in Indonesian Social Media. Procedia Computer Science 2018;135:222-229." (https://github.com/okkyibrohim/id-abusive-language-detection.git)')
                    ])
           
        ]
        )
    ], content_style = {
        'fontFamily' : 'Arial',
        'borderBottom' : '1px solid #d6d6d6',
        'borderLeft' : '1px solid #d6d6d6',
        'borderRight' : '1px solid #d6d6d6',
        'padding' : '44px'
    })

    ],
    style = {
    'maxWidth': '1100px',
    'margin' : '0 auto'
}
)


# Update twitter dashboard
@app.callback([Output('live-update-graph', 'children'),
               Output('live-update-table', 'children'),
               Output('live-update-influencer', 'children'),
               Output('positive-graph', 'children'),
               Output('negative-graph','children')],
              [Input('interval-component', 'n_intervals')],
               [State('search-keyword', 'children')])

def update_metrics(n, x1):
    print ('execute')
    temp = append_db(x1,100)
    data = pd.DataFrame(temp, 
            columns = ['index','created_at','source','text','user_id','user_screen_name','user_name','user_created_at','user_follower_count', 'text_clean','sentimen','sentimen_neg'])
    data.index = data['index']
    data.drop('index', axis = 1, inplace = True)
    data['created_at'] = pd.to_datetime(data['created_at'], utc = True)
    data['user_created_at'] = pd.to_datetime(data['user_created_at'], utc = True)
    data_display = data[['created_at','user_screen_name','text', 'sentimen']]
    data_display = data_display.sort_values(by = 'created_at', ascending = False)
    data['created_at'] = data['created_at'].apply(lambda x : x.replace(second = 0, microsecond=0))
    group = data.groupby('created_at')

    tab = dash_table.DataTable(
                id='form-table',
                columns=[{"name": i, "id": i} for i in data_display.columns],
                data=data_display.to_dict('records'),
                style_table={'overflowX': 'scroll'},
                fixed_rows={ 'headers': True, 'data': 0 },
                style_cell={
                    'height': 'auto',
                    # all three widths are needed
                    # 'minWidth': '80px', 'width': '180px', 'maxWidth': '240px',
                    'minWidth': '80px', 'width': '180px', 'maxWidth': '240px',
                    'whiteSpace': 'normal'
                }

            )

    graph = dcc.Graph(
                id='twitter-counter-chart',
                figure = {
                'data': [
                    go.Bar(x = group.count().index, y = group.count()['text'], name = 'total'),
                    go.Scatter(x = group.count().index, y = group.sum()['sentimen'], mode = 'lines', name = 'positive'),
                    go.Scatter(x = group.count().index, y = group.sum()['sentimen_neg'], mode = 'lines', name = 'negative')

                    # {'x': group.count().index, 'y': group.count()['text'], 'type': 'line', 'marker' : '*', 'name': 'total'},
                    # {'x': group.count().index, 'y': group.sum()['sentimen'], 'type': 'line', 'name': 'positive'},
                    # {'x': group.count().index, 'y': group.sum()['sentimen_neg'], 'type': 'line', 'name': 'negative'}
                ],
                'layout': {'title': "Tweet's about {}".format(x1)}
            }
    )
    ## add 
    
    bargraphY_list = list(data['user_screen_name'].value_counts().head(10).sort_values().index)
    
    hovertext = []
    bargraphX_list_pos = []
    bargraphX_list_neg = []
    for y in bargraphY_list:
        hovertext.append('@{}, follower = {}'.format(y,data[data['user_screen_name'] == y]['user_follower_count'].values[0]))
        temp = data.groupby('user_screen_name')
        bargraphX_list_pos.append(temp.sum().loc[y]['sentimen'])
        bargraphX_list_neg.append(temp.sum().loc[y]['sentimen_neg'])
    
 

    tweet_user = dcc.Graph(
                id='total-bar-chart',
                figure = {
                'data': [
                    {'x': bargraphX_list_neg,
                     'y': bargraphY_list,
                      'type': 'bar', 'name': 'positive', 'orientation' : 'h',
                      'hovertext' : hovertext
                      },
                      {'x': bargraphX_list_pos,
                     'y': bargraphY_list,
                      'type': 'bar', 'name': 'negative', 'orientation' : 'h',
                      'hovertext' : hovertext
                      }
                ],
                'layout': {'title': 'User with most tweets about {}'.format(x1), 'barmode' : 'stack'}
            }
    )

    word_positive = word_extract(data[data['sentimen'] == 1]['text_clean'])
    word_negative = word_extract(data[data['sentimen'] == 0]['text_clean'])

    a_positive = nltk.FreqDist(word_positive)
    d_positive = pd.DataFrame({'Hashtag': list(a_positive.keys()),
                    'Count': list(a_positive.values())})
    d_positive = d_positive[d_positive['Hashtag'] != x1]
    # selecting top 10 most frequent hashtags     
    d_positive = d_positive.nlargest(columns="Count", n = 10) 

    positive_graph = dcc.Graph(
                id='Positive-word-chart',
                figure = {
                'data': [
                    go.Bar(x = d_positive['Hashtag'], y = d_positive['Count'], name = 'positive_word'),
                    
                    # {'x': group.count().index, 'y': group.count()['text'], 'type': 'line', 'marker' : '*', 'name': 'total'},
                    # {'x': group.count().index, 'y': group.sum()['sentimen'], 'type': 'line', 'name': 'positive'},
                    # {'x': group.count().index, 'y': group.sum()['sentimen_neg'], 'type': 'line', 'name': 'negative'}
                ],
                'layout': {'title': "Positive Word About {}".format(x1)}
            }
    )

    a_negative = nltk.FreqDist(word_negative)
    d_negative = pd.DataFrame({'Hashtag': list(a_negative.keys()),
                    'Count': list(a_negative.values())})
    # selecting top 10 most frequent hashtags  
    d_negative = d_negative[d_negative['Hashtag'] != x1]   
    d_negative = d_negative.nlargest(columns="Count", n = 10)

    negative_graph = dcc.Graph(
                id='Negative-word-chart',
                figure = {
                'data': [
                    go.Bar(x = d_negative['Hashtag'], y = d_negative['Count'], name = 'negative_word'),
                    
                    # {'x': group.count().index, 'y': group.count()['text'], 'type': 'line', 'marker' : '*', 'name': 'total'},
                    # {'x': group.count().index, 'y': group.sum()['sentimen'], 'type': 'line', 'name': 'positive'},
                    # {'x': group.count().index, 'y': group.sum()['sentimen_neg'], 'type': 'line', 'name': 'negative'}
                ],
                'layout': {'title': "Negative Word About {}".format(x1)}
            }
    )

    return graph , tab, tweet_user, positive_graph, negative_graph


## Update search keyword
@app.callback(
    Output(component_id = 'search-keyword', component_property = 'children'),
    [Input(component_id = 'search-tweet', component_property = 'n_clicks')],
    [State(component_id = 'search-tweet-bar', component_property = 'value')]
)

def search_tweet(n_clicks, x1):
    return x1



## Check tweet
@app.callback(
    [Output(component_id = 'result-sentimen', component_property = 'children')],
    [Input(component_id = 'check-tweet', component_property = 'n_clicks')],
    [State(component_id = 'tweet-bar', component_property = 'value')]
)

def check_tweet(n_clicks, x1):
    x1 = text_process(x1)
    predict = loadModel.predict([x1])
    if predict[0] == 1:
        return [html.H4(':D')]
    else:
        return [html.H4(':(')]

    


if __name__ == '__main__':
    app.run_server(debug = True)


