import os
from dotenv import load_dotenv

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors

from googleapiclient.discovery import build

import os

import csv

# Globals
api_service_name = "youtube"
api_version = "v3"
load_dotenv()
api_key = os.getenv('api_key')
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
    channel_Id = {}
    with open('data/channels.txt', 'r') as channels:
        for channel in channels:
            handle = channel.strip()
            if not handle:
                continue
            try:
                request = youtube.channels().list(
                    part="snippet,contentDetails,statistics",
                    forHandle=handle
                )
                response = request.execute()
                if response['items']:
                    channel_Id[handle] = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
                else:
                    print(f"No channel found for handle: {handle}")
            except Exception as e:
                print(f"Error for {handle}: {e}")
                continue
    return channel_Id

# note: cost of this operation is 100 units of the alloted 10,000 units per 24 hours
def getVideoIDsFromPlaylist(playlist_id, max_results=10):
    video_ids = []
    nextPageToken = None
    while len(video_ids) < max_results:
        try:
            request = youtube.playlistItems().list(
                part="contentDetails",
                playlistId=playlist_id,
                maxResults=min(50, max_results - len(video_ids)),
                pageToken=nextPageToken
            )
            response = request.execute()
            for item in response.get('items', []):
                video_id = item['contentDetails']['videoId']
                video_ids.append(video_id)
            nextPageToken = response.get('nextPageToken')
            if not nextPageToken:
                break
        except Exception as e:
            print(f"Error fetching videos from playlist {playlist_id}: {e}")
            break
    return video_ids

# Collect comments for each video and write to CSV
def load_ids_from_csv(csv_path, id_col):
    ids = set()
    if not os.path.exists(csv_path):
        return ids
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ids.add(row[id_col])
    return ids

def save_ids_to_csv(csv_path, ids, header):
    mode = 'a' if os.path.exists(csv_path) else 'w'
    with open(csv_path, mode, newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if mode == 'w':
            writer.writerow(header)
        for id_val in ids:
            writer.writerow([id_val])

def collect_and_write_comments(video_ids, csv_path='data/yt_comments.csv', video_log='data/collected_videos.csv', comment_log='data/collected_comments.csv'):
    collected_videos = load_ids_from_csv(video_log, 'video_id')
    collected_comments = load_ids_from_csv(comment_log, 'comment_id')
    new_videos = set()
    new_comments = set()
    with open(csv_path, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        # Write header if file is empty
        if csvfile.tell() == 0:
            writer.writerow([
                'video_id', 'comment_id', 'author_display_name', 'published_at',
                'like_count', 'comment_text', 'is_reply', 'parent_id', 'channel_id'
            ])
        for video_id in video_ids:
            if video_id in collected_videos:
                print(f"Skipping already collected video: {video_id}")
                continue
            nextPageToken = None
            while True:
                try:
                    request = youtube.commentThreads().list(
                        part="snippet,replies",
                        maxResults=100,
                        order="time",
                        textFormat="plainText",
                        videoId=video_id,
                        pageToken=nextPageToken
                    )
                    response = request.execute()
                    for item in response.get('items', []):
                        comment_id = item['id']
                        if comment_id in collected_comments:
                            continue
                        snippet = item['snippet']['topLevelComment']['snippet']
                        writer.writerow([
                            video_id,
                            comment_id,
                            snippet.get('authorDisplayName', ''),
                            snippet.get('publishedAt', ''),
                            snippet.get('likeCount', 0),
                            snippet.get('textDisplay', ''),
                            0, # is_reply (top-level)
                            '', # parent_id
                            snippet.get('authorChannelId', {}).get('value', '')
                        ])
                        new_comments.add(comment_id)
                        # Write replies if present
                        for reply in item.get('replies', {}).get('comments', []):
                            reply_id = reply['id']
                            if reply_id in collected_comments:
                                continue
                            reply_snippet = reply['snippet']
                            writer.writerow([
                                video_id,
                                reply_id,
                                reply_snippet.get('authorDisplayName', ''),
                                reply_snippet.get('publishedAt', ''),
                                reply_snippet.get('likeCount', 0),
                                reply_snippet.get('textDisplay', ''),
                                1, # is_reply
                                reply_snippet.get('parentId', ''),
                                reply_snippet.get('authorChannelId', {}).get('value', '')
                            ])
                            new_comments.add(reply_id)
                    nextPageToken = response.get('nextPageToken')
                    if not nextPageToken:
                        break
                except Exception as e:
                    print(f"Error fetching comments for video {video_id}: {e}")
                    break
            new_videos.add(video_id)
    # Save new video and comment IDs
    if new_videos:
        save_ids_to_csv(video_log, new_videos, ['video_id'])
    if new_comments:
        save_ids_to_csv(comment_log, new_comments, ['comment_id'])

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
    # Full workflow: get channels, get videos, get comments
    channels = getChannel()
    for handle, playlist_id in channels.items():
        print(f"Processing channel: {handle}")
        video_ids = getVideoIDsFromPlaylist(playlist_id, max_results=10)
        print(f"  Found {len(video_ids)} videos.")
        collect_and_write_comments(video_ids)
    print("Done collecting comments.")

if __name__ == "__main__":
    main()