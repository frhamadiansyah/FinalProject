import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go
import pandas as pd
import datetime
import time
from twitter import Twitter, OAuth
from sqlalchemy import create_engine
from bs4 import BeautifulSoup
import string
from nltk.corpus import stopwords
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
import re
import pickle

kamus_alay = pd.read_csv("kamus_slang.csv", index_col = 0)

kamus = {}
# kamus_alay[kamus_alay['Alay'] == 'gw']
for index, row in kamus_alay.iterrows():
    kamus[row['Alay']] = row['KBBI']


loadModel = pickle.load(open('linearsvc_binary(1).sav', 'rb'))


def text_process(text):
    ##Clean_Link
    
    #lowercase all
    text = text.lower()
    #hapus RT

    text=re.sub(r'^rt @[^\s]+','',text)
    #hapus @

    text=re.sub(r'@\S+','',text)
    
    #text = re.sub(',','',text)
    text=re.sub(r'http\S+','',text)
    #hapus \n
    text=re.sub('\n',' ',text)
    #hapus hashtag
    text = re.sub(r'#\S+','',text)
    
    ## hapus punc
    hapus = string.punctuation + '0123456789'
    text = [char for char in text if char not in hapus]
    text = ''.join(text)
    
    def hapus_hurufdouble(s): 
        #look for 2 or more repetitions of character and replace with the character itself
        pattern = re.compile(r"(.)\1{1,}", re.DOTALL)
        return pattern.sub(r"\1\1", s)
    
    ## Substitute slang
    text = [hapus_hurufdouble(word) for word in text.split()]
    global kamus
    for i in range(len(text)):
        if text[i] in kamus.keys():
            text[i] = kamus[text[i]]
    
    
    ## Stemming
    factory = StemmerFactory()
    stemmer = factory.create_stemmer()

    ## Hapus stop words
    return ' '.join([stemmer.stem(word) for word in text if word not in stopwords.words('indonesian')])

# def text_process(text):
#     ##Clean_Link
    
#     #lowercase all
#     text = text.lower()
#     #hapus RT

#     text=re.sub(r'^rt @[^\s]+','',text)
#     #hapus @

#     text=re.sub(r'@\S+','',text)
    
#     #text = re.sub(',','',text)
#     text=re.sub(r'http\S+','',text)
#     #hapus \n
#     text=re.sub('\n',' ',text)
#     #hapus hashtag
#     text = re.sub(r'#\S+','',text)
    
#     ## hapus punc
#     hapus = string.punctuation + '0123456789'
#     text = [char for char in text if char not in hapus]
#     return ''.join(text)
    
    