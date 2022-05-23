from flask import Flask, session, render_template, url_for, request, redirect , flash
from pandas.core.frame import DataFrame
import os, json, re
from datetime import datetime
from apiclient.discovery import build
from csv import writer
from ibm_watson import NaturalLanguageUnderstandingV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson.natural_language_understanding_v1 import Features,CategoriesOptions,EmotionOptions,KeywordsOptions
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from urllib import parse
import math

IAM_KEY = '7FMCZ0dUQcOepAv0cFxNQh8HZSY0MqFsHqHoo0l9Cscr'
SERVICE_URL = 'https://api.us-south.natural-language-understanding.watson.cloud.ibm.com/instances/027f47fc-8454-4bc1-b47a-4b21de42c703'


authenticator = IAMAuthenticator(IAM_KEY)
natural_language_understanding = NaturalLanguageUnderstandingV1(version='2020-08-01',authenticator=authenticator)

natural_language_understanding.set_service_url(SERVICE_URL)
video_title=""
def build_service():
#You should access to YoutubeApi to obtain the key
    key = "AIzaSyB2C2LQVDOhU3YeUEwU-Haxz0ZBdIP6A0g"
    YOUTUBE_API_SERVICE_NAME = "youtube"
    YOUTUBE_API_VERSION = "v3"
    return build(YOUTUBE_API_SERVICE_NAME,YOUTUBE_API_VERSION,developerKey=key)
#example youtube video : https://www.youtube.com/watch?v=t0UmUGGVgsU

#url_data = urlparse.urlparse("https://www.youtube.com/watch?v=NWPkZ9HAQ9M&ab_channel=iizcat")
#query = urlparse.parse_qs(url_data.query)
#video = query["v"][0]

def get_comments(part, 
                 maxResults, 
                 textFormat,
                 order,
                 videoId,
				 #videoId=video,
                 csv_filename):

    #3 create empty lists to store desired information
    comments, authors,sources, dates = [], [], [], []
    # build our service from path/to/apikey
    service = build_service()
    video_request=service.videos().list(
    part='snippet,statistics',
    id=videoId
    )
    try:
        video_response = video_request.execute()
        #print(video_response['items'])
        video_items=video_response['items']
        video_snippetT= video_items[0]
        video_snippet=video_snippetT['snippet']
    # print(video_snippet['title'])
        video_title=video_snippet['title']
        print(video_title)
    except:
        session.pop('_flashes')
        flash('It is not YouTube url!','error')
        redirect('/')
    #4 make an API call using our service
    response = service.commentThreads().list(part=part, maxResults=maxResults, textFormat=textFormat, order=order, videoId=videoId).execute()
    h="Time,author,Comment"
    with open('data.csv','a+',encoding='utf-8-sig') as f:
        f.truncate(0)
        csv_writer = writer(f)
        csv_writer.writerow(['Comment'])
    while response: # this loop will continue to run until you max out your quota
                 
        for item in response['items']:
            #4 index item for desired data features
            comment1 = item['snippet']['topLevelComment']['snippet']
            comment = comment1['textDisplay'].replace('\n', '')
            #comment=re.sub("[^A-Za-z,.!?']"," ",comment)
            author = comment1['authorDisplayName']
            date = comment1['publishedAt']
            source = comment1['videoId']
            
            #4 append to lists
            comments.append(comment)
            authors.append(author)
            sources.append(source)
            dates.append(date)
			

            #7 write line by line
            with open('data.csv','a+',encoding='utf-8-sig') as f:
                # write the data in csv file with colums(source, date, author, text of comment)
                csv_writer = writer(f)
                comment = re.sub(':\S+?:', ' ', comment)
                csv_writer.writerow([comment])
                
             #8 check for nextPageToken, and if it exists, set response equal to the JSON response
        if 'nextPageToken' in response:
            response = service.commentThreads().list(
                part=part,
                maxResults=maxResults,
                textFormat=textFormat,
                order=order,
                videoId=videoId,
                pageToken=response['nextPageToken']
            ).execute()
        else:
            break
        

    #9 return our data of interest
    return video_title





app = Flask(__name__)
app.secret_key='ff1e5c4920b92ca16cac5b7cbd0765e9'






@app.route('/analyze' , methods=['GET', 'POST'])
def analyze():
    if request.method == 'POST':
        
        url = request.form['url']
        
        Vid=""
    #url = "https://www.youtube.com/watch?v=HW367HtrXE0&ab_channel=Audiotree"
        try:
            url_parsed = parse.urlparse(url)
            qsl = parse.parse_qs(url_parsed.query)
            Vid=str(qsl["v"]).split("'")[1]
        except:
            #session['_flashes'].clear()
            session.pop('_flashes')
            flash('It is not YouTube url!','error')
            print(session)
            redirect('/')
            #return 'It is not YouTube url!'
        video_title=get_comments(part='snippet', 
                    maxResults=200, 
                    textFormat='plainText',
                    order='time',
                    #videoId='EG_kUsgr9PI',
                    videoId=Vid,
                    csv_filename="data")
                    
        df = pd.read_csv('data.csv')
        df.head(10)
        text1 = df.loc[3,"Comment"]
        text1

        df2=df['Comment'].dropna(how = 'all')
        df2.head(10)
        df_text = df2.to_string()
        df_text = re.sub(':\S+?:', ' ', df_text)
        df_text

        df2 =df2.replace(regex=['X+'],value='')
        df_text = df2.to_string()
        df_text


        response = natural_language_understanding.analyze(
            text = df_text,
            features=Features(keywords=KeywordsOptions(sentiment=True,emotion=True,limit=200))).get_result()
        print(response)

        total_score=0
        countable=0
        avg=0.0
        score_result=[]
        toptext={}
        emotions=[]
        bulit_result={}
        positive_rate=0.0
        negative_rate=0.0
        neutral_rate=0.0
        positive_count=0
        negative_count=0
        neutral_count=0
        sorted_response= {}
        sorted_response =  sorted(response['keywords'], key = lambda i: i['count'],reverse=True)
        print(sorted_response)
        for item in sorted_response :
            #print (item['sentiment'])
            #print (item['emotion'])
            print (item)        
            count=item['count']
            comments_score=item['sentiment']
            if response['language'] == 'zh':
                #bulit_result=item['emotion']
                bulit_result={}
                bulit_result.setdefault('text',item['text'])
                bulit_result.setdefault('count',count)
                emotions.append(bulit_result)
            if response['language'] == 'en':
                bulit_result=item['emotion']
                bulit_result.setdefault('text',item['text'])
                bulit_result.setdefault('count',count)
                emotions.append(bulit_result)
            
            
            
            #if comments_score['score'] !=0:
            if count==1:
                break
            total_score+=comments_score['score']
            countable+=1
            if comments_score['label']=='positive':
                positive_count=positive_count+1
            if comments_score['label']=='negative':
                negative_count=negative_count+1
            if comments_score['label']=='neutral':
                neutral_count=neutral_count+1
        print (emotions)
        avg=total_score/countable
        positive_rate=positive_count/countable*100
        negative_rate=negative_count/countable*100
        neutral_rate=neutral_count/countable*100   
        
        score_result.append(round(avg,2))
        score_result.append(round(positive_rate,2))
        score_result.append(round(negative_rate,2))
        score_result.append(round(neutral_rate,2))
        result=json.dumps(response, indent=2)
        print(avg)
        #sorted_df = test_df.sort_values(by='sentiment.score', ascending=False)
        #sorted_emotions=emotions.sort_values(by='count', ascending=False)
        
    # sorted_emotions =  sorted(emotions,'count', reverse=True)
        # 
        print(video_title)
    else:
        return 'ERROR URL'
    return render_template('result.html', score = score_result,data=emotions,Vtitle= video_title)

@app.route('/about')
def about():
    return render_template('about.html')
@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')
@app.errorhandler(500)
def internal_error(error):
    flash('It is not YouTube url!','error')
    return render_template('index.html'), 500
port = int(os.getenv('PORT',8080))

if __name__=='__main__':
    app.run(host='0.0.0.0',port=port) 
