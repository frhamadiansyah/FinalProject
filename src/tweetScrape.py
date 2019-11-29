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
# from sqlalchemy import create_engine
from bs4 import BeautifulSoup
import pickle
# from src.text_process import text_process, loadModel
# from PIL import Image
# from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
import string
from nltk.corpus import stopwords
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
import re

# engine = create_engine('mysql+mysqlconnector://root:Fandri54@localhost/twitter?host=localhost?port=3306')
# conn = engine.connect()
# print(conn)
ACCESS_TOKEN = ''
ACCESS_SECRET = ''
CONSUMER_KEY = ''
CONSUMER_SECRET = ''

oauth = OAuth (ACCESS_TOKEN, ACCESS_SECRET, CONSUMER_KEY, CONSUMER_SECRET)

twitter = Twitter(auth = oauth)


loadModel = pickle.load(open('linearsvc_binary(1).sav', 'rb'))

kamus_alay = pd.read_csv("kamus_slang.csv", index_col = 0)

kamus = {}
# kamus_alay[kamus_alay['Alay'] == 'gw']
for index, row in kamus_alay.iterrows():
    kamus[row['Alay']] = row['KBBI']

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



def create_tweet_df(search, n):
    tweets = twitter.search.tweets(q=search,result_type = 'top', count = n, lang = 'id')
    df = pd.DataFrame(tweets['statuses'])
    df['user_id'] = df['user'].apply(lambda x : x['id'])
    df['user_screen_name'] = df['user'].apply(lambda x : x['screen_name'])
    df['user_name'] = df['user'].apply(lambda x : x['name'])
    df['user_created_at'] = df['user'].apply(lambda x : x['created_at'])
    df['user_follower_count'] = df['user'].apply(lambda x : x['followers_count'])
    
    df.drop('user',axis = 1, inplace = True)

    def clean_source(src):
        soup = BeautifulSoup(src, 'html.parser')
        return soup.text

    df['source'] = df['source'].apply(clean_source)
    df['created_at'] = pd.to_datetime(df['created_at'], utc = True)
    df['user_created_at'] = pd.to_datetime(df['user_created_at'], utc = True)
    
    #clean text
    df = df[['created_at','source','text','user_id','user_screen_name','user_name','user_created_at','user_follower_count']]

    return df

def clean_and_predict(df):
    
    df['text_clean'] = df['text'].apply(text_process)
    ## add sentimen
    df['sentimen'] = df['text_clean'].apply(lambda x : loadModel.predict([x])[0])
    
    def sentimen_neg(x):
        if x == 0:
            return 1
        else:
            return 0
    
    df['sentimen_neg'] = df['sentimen'].apply(sentimen_neg)

    return df

database = {}

def append_db(search, n):
    total = create_tweet_df(search,n)
    search = '_'.join(search.split())
    global database
    # print(total.columns)
    # tableName = search+'_'+str(datetime.datetime.now().day)+str(datetime.datetime.now().month)+str(datetime.datetime.now().year)    
    if search in database.keys() :
        print('try')
        all_db = database[search]
        # all_db = conn.execute('select * from {}'.format(tableName)).fetchall()
        print ('succeed')
        # all_db = pd.DataFrame(all_db, columns = ['index','created_at','source','text','user_id','user_screen_name','user_name','user_created_at','user_follower_count', 'text_clean','sentimen','sentimen_neg'])
        # all_db.index = all_db['index']
        # all_db.drop('index', axis = 1, inplace = True)
        # all_db['created_at'] = pd.to_datetime(all_db['created_at'], utc = True)
        temp = total[total['created_at'] > all_db['created_at'].max()]
        if (len(temp) > 0) & ((total['created_at'].min() - all_db['created_at'].max()).seconds <= 120):
            # conn.execute('ALTER TABLE {}'.format(tableName))
            temp = clean_and_predict(temp)
            temp = temp.sort_values(by = 'created_at')
            # print(temp.columns)
            # temp.to_sql(con=conn, name=tableName, if_exists='append') #
            database[search] = pd.concat([all_db, temp], ignore_index = True)
            print('add')
            if len(database[search]) > 1000:
                return database[search].tail(1000)
            else:
               return database[search]
        elif (len(temp) > 0) & ((total['created_at'].min() - all_db['created_at'].max()).seconds >= 120): 
            temp = clean_and_predict(temp)
            temp = temp.sort_values(by = 'created_at')
            database[search] = temp
            print('gap')
            return database[search]
        else :
            return database[search]
            # return temp

    else :
        print ('alternative')
        total = clean_and_predict(total)
        print ('clean')
        total = total.sort_values(by = 'created_at')
        # total.to_sql(con=conn, name=tableName) #
        database[search] = total
        print('complete')
        return database[search]



# def append_db(search, n):
#     total = create_tweet_df(search,n)
#     search = '_'.join(search.split())
#     global database
#     # print(total.columns)
#     tableName = search+'_'+str(datetime.datetime.now().day)+str(datetime.datetime.now().month)+str(datetime.datetime.now().year)    
#     try :
#         print('try')
#         all_db = conn.execute('select * from {}'.format(tableName)).fetchall()
#         print ('succeed')
#         all_db = pd.DataFrame(all_db, columns = ['index','created_at','source','text','user_id','user_screen_name','user_name','user_created_at','user_follower_count', 'text_clean','sentimen','sentimen_neg'])
#         all_db.index = all_db['index']
#         all_db.drop('index', axis = 1, inplace = True)
#         all_db['created_at'] = pd.to_datetime(all_db['created_at'], utc = True)
#         temp = total[total['created_at'] > all_db['created_at'].max()]
#         if len(temp) > 0:
#             conn.execute('ALTER TABLE {}'.format(tableName))
#             temp = clean_and_predict(temp)
#             temp = temp.sort_values(by = 'created_at')
#             # print(temp.columns)
#             temp.to_sql(con=conn, name=tableName, if_exists='append') #
#             print('add')
#             return conn.execute('select * from {}'.format(tableName)).fetchall()
#         else :
#             return conn.execute('select * from {}'.format(tableName)).fetchall()
#             # return temp

#     except :
#         print ('alternative')
#         total = clean_and_predict(total)
#         print ('clean')
#         total = total.sort_values(by = 'created_at')
#         total.to_sql(con=conn, name=tableName) #
#         print('complete')
#         return conn.execute('select * from {}'.format(tableName)).fetchall()


    # except :
    #     total = total.sort_values(by = 'created_at')
    #     total.to_sql(con=conn, name=tableName, if_exists='append')
    #     return conn.execute('select * from {}'.format(tableName)).fetchall()


    # conn.execute('ALTER TABLE {} ADD id INT NOT NULL AUTO_INCREMENT PRIMARY KEY'.format(tableName))
    # conn.execute('ALTER TABLE {}'.format(tableName))
    # # while total.shape[0] < n:
    # #     time.sleep(10)
    # #     temp = create_tweet_df(search,n)
    # #     temp_1 = temp[(temp['created_at']) > (total['created_at'].max())]
    # #     if temp_1.shape[0] >0:
    # #         temp_1.to_sql(con=conn, name=tableName, if_exists='append')
    # #         total = pd.concat([total,temp_1], axis = 0)

    # all_db = conn.execute('select * from {}'.format(tableName)).fetchall()

    # return all_db



# append_db('trump',100)
# db = append_db('trump',100)
# data = pd.DataFrame(db, columns = ['index', 'created_at', 'source', 'text', 'user_id', 'user_screen_name', 'user_name', 'user_created_at', 'user_follower_count'])
# df = data[['created_at','user_screen_name','text']]
# print(df)
# append_db('jokowi',100)
# # time.sleep(60)
# # append_db('jokowi',100)
# time.sleep(240)
# append_db('jokowi',100)

# def word_cloud_positive(df, column):
#     plt.figure(figsize = (12,8))
#     text = " ".join(review for review in df[df['sentimen'] == 1][column])

#     # Create and generate a word cloud image:
#     wordcloud = WordCloud().generate(text)

#     # Display the generated image:
#     plt.imshow(wordcloud, interpolation='bilinear')
#     plt.axis("off")
#     plt.show()
#     plt.savefig('positive_cloud.png')