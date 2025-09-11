import os
from dotenv import load_dotenv

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors

from googleapiclient.discovery import build

import requests, sys, time, os, argparse

# Globals
api_service_name = "youtube"
api_version = "v3"
load_dotenv()
api_key = os.getenv('key')
global youtube
youtube = build(api_service_name, api_version, developerKey=api_key)

# @TODO
# get channel -> get uploads playlist id -> get ~10 videos -> get max 100 comments using threads per video

""" 
9-4-2025

for now the top priority is getting the comments, i think its a good idea to consider channel & video metrics in the future though..
you dont use the channelID to seach for videos, theres another Id that is a playlist of all the channel's uploaded vids,
we will use this. getChannel() grabs the uploaded vids playlist Id for each channel, we get a chanel uing the @handle(we dont need the @ just plaintext is fine)

next task is finding a good way to collect a batch of videos for each playlist... when we're doing 100's of videos and comments that will add up time and resource wise so lets just make it easier for future us now and come up with an efficient way now
 """

# grabbing channels by their '@' handle may be the easiest if we have a predefined list of channels we want
def getChannel():
    channel_Id = []
    with open('data/channels.txt', 'r') as channels:
        for channel in channels:
            try:
                request = youtube.channels().list(
                part="snippet,contentDetails,statistics",
                forHandle=channel
                )
                response = request.execute()
            
                channel_Id.append(response['items'][0]['contentDetails']['relatedPlaylists']['uploads'])
            except:
                print(channel + " not found")
                continue
            
    return channel_Id

# @TODO grab a batch of videos for each playlist then grab <= 100 comment threads per video
def getTen(playlist, batch):
    videos = []
    for video in range(batch):
        videos.append(video)
    return videos

# note: cost of this operation is 100 units of the alloted 10,000 units per 24 hours
def getVideos(topic):
    playlists = getChannel()
    
    for playlist in playlists:
        vids_Added = 0
        
        if vids_Added == 10:
            vids_Added = 10
            current += 1
        
        
        request = youtube.search().list(
            part="id,snippet",
            maxResults=5,
            q=topic
        )
    return request.execute()

# collect & save videoIDs
def populateVideoIDs(videos):
    videoIDs = []
    for video in videos:
        if('videoId' in video['id']):
            videoIDs.append(video['id']['videoId'])
    return videoIDs

# @TODO change method to fit our needs
def collectVideoData(videos):
    collection_of_video_data = {}
    for video in videos:
        if('videoId' in video['id']):
            request = youtube.videos().list(part = 'snippet, statistics', id = video['id']['videoId'])
            response = request.execute()
            collection_of_video_data[video['id']['videoId']] = response
    return collection_of_video_data

# call api to collect data per comment thread
def collectVideoComment(videos):
    
    for video in videos:
        if('videoId' in video['id']):
            request = youtube.commentThreads().list(
                part="snippet,replies",
                maxResults=5,
                order="time",
                textFormat="html",
                videoId="_VB39Jo8mAQ"
            )
            response = request.execute()
    return response

def testAPI():
    request = youtube.channels().list(
        part="snippet,contentDetails,statistics",
        id="UC_x5XG1OV2P6uZZ5FSM9Ttw"
    )
    response = request.execute()

    print('\n\n\n' + 'REQUESTED' + '\n\n\n')
    
    try:
        print(response)
        print('\n\n\n' + 'REQUEST SUCCESS!' + '\n\n\n')    
    except:
        print('\n\n\n' + 'REQUEST FAILED' + '\n\n\n')
        
def main():
    
    print(getChannel())
    return

if __name__ == "__main__":
    main()