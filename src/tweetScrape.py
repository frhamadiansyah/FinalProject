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
import pickle
from src.text_process import text_process, loadModel
from PIL import Image
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
import matplotlib.pyplot as plt

engine = create_engine('mysql+mysqlconnector://root:Fandri54@localhost/twitter?host=localhost?port=3306')
conn = engine.connect()
# print(conn)
ACCESS_TOKEN = '68150221-OzSdaX7aQODB1CvWNrcyU6fRvqw6miJkUIKJ9ixuR'
ACCESS_SECRET = '6HS4Jhs2BpbiQ56BjVKqooxpt59yAkd14QfTx8Ymt6Q5E'
CONSUMER_KEY = 'YqdIu04vS4rVeZC9qUixfV9G0'
CONSUMER_SECRET = 'IIVZ1Twfr8Qcdk89PEYHJg8NKP9mB8UTyGsYOikhdYqnvbCu92'

oauth = OAuth (ACCESS_TOKEN, ACCESS_SECRET, CONSUMER_KEY, CONSUMER_SECRET)

twitter = Twitter(auth = oauth)


loadModel = pickle.load(open('linearsvc_binary.sav', 'rb'))




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



def append_db(search, n):
    total = create_tweet_df(search,n)
    search = '_'.join(search.split())
    # print(total.columns)
    tableName = search+'_'+str(datetime.datetime.now().day)+str(datetime.datetime.now().month)+str(datetime.datetime.now().year)    
    try :
        print('try')
        all_db = conn.execute('select * from {}'.format(tableName)).fetchall()
        print ('succeed')
        all_db = pd.DataFrame(all_db, columns = ['index','created_at','source','text','user_id','user_screen_name','user_name','user_created_at','user_follower_count', 'text_clean','sentimen','sentimen_neg'])
        all_db.index = all_db['index']
        all_db.drop('index', axis = 1, inplace = True)
        all_db['created_at'] = pd.to_datetime(all_db['created_at'], utc = True)
        temp = total[total['created_at'] > all_db['created_at'].max()]
        if len(temp) > 0:
            conn.execute('ALTER TABLE {}'.format(tableName))
            temp = clean_and_predict(temp)
            temp = temp.sort_values(by = 'created_at')
            # print(temp.columns)
            temp.to_sql(con=conn, name=tableName, if_exists='append') #
            return conn.execute('select * from {}'.format(tableName)).fetchall()
        else :
            return conn.execute('select * from {}'.format(tableName)).fetchall()
            # return temp

    except :
        print ('alternative')
        total = clean_and_predict(total)
        print ('clean')
        total = total.sort_values(by = 'created_at')
        total.to_sql(con=conn, name=tableName) #
        print('complete')
        return conn.execute('select * from {}'.format(tableName)).fetchall()


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
# print(append_db('ahok',100))

def word_cloud_positive(df, column):
    plt.figure(figsize = (12,8))
    text = " ".join(review for review in df[df['sentimen'] == 1][column])

    # Create and generate a word cloud image:
    wordcloud = WordCloud().generate(text)

    # Display the generated image:
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis("off")
    plt.show()
    plt.savefig('positive_cloud.png')