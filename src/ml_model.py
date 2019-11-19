import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go
import pickle
import numpy as np
from sklearn.preprocessing import LabelEncoder

loadModel = pickle.load(open('legendary_predictor.sav', 'rb'))

def legendary_predictor(total,attack,defense,gen):
    stats = np.array([total, attack, defense, gen]).reshape(1,-1)
    legendproba = loadModel.predict_proba(stats)[0]
    if total == 0 & attack == 0 & defense == 0 & gen == 0:
        return 'Fill in stats value'
    elif legendproba[0] > legendproba[1]:
        return 'Your Pokemon is Not-Legendary with probability {}'.format(legendproba[0])
    else : 
        return 'Your Pokemon is Legendary with probability {}'.format(legendproba[1])
