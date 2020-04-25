import re
from flask import Flask, render_template, url_for, json
import json
import pprint
from app.irsystem.models.helpers import *
import random
import requests
import os
import praw
import time
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from bs4 import BeautifulSoup

class RedditData():
    def __init__(self):
        '''
        self.FOLDER_NAME: folder where all reddit related json data is stored
        self.DATA_ROOT: Path to self.FOLDER_NAME
        self.STATIC_DATA_PATH: Entire path including where self.FOLDER_NAME is
        self.reddit_list: List of reddit results formatted as described in getCaseListFromFile()
        self.reddit_dict: Dict of reddit results indexed on case id
        self.ids_cases_pair: Tuple of lists as identified in getCleanReddit(), utilized in tfidf
        '''
        self.FOLDER_NAME = 'reddit_data'
        self.DATA_ROOT = os.path.realpath(os.path.dirname('app/data/' + self.FOLDER_NAME))
        self.STATIC_DATA_PATH = os.listdir(os.path.join(self.DATA_ROOT, self.FOLDER_NAME))
        self.reddit_list = self.getRedditList()
        self.reddit_dict = self.getRedditDict()
        self.ids_reddit_pair = self.getCleanReddit()

    def getCleanReddit(self):
        '''
        Preprocesses reddit results to extract and concat reddit titles and body

        Parameters:
            self.reddit_list:
                [
                    ('reddit title', 'description', 'id', 'url'),
                    ...
                ],
        Returns:
            tuple of lists, where the first element is a list of reddit IDs and
            the second element is an array where each element is the corresponding text
            (title and body text concatenated together) for that reddit result.
        '''
        ret = ([], [])
        for elem in self.reddit_list:
            text_str = cleanText(removeHTML(elem[0] + ' ' + elem[1]))
            ret[0].append(str(elem[2]))
            ret[1].append(text_str)
        return ret

    # TODO: Delete this function and replace with a fully implemented getRedditListFromFile()
    def getRedditListFromAPI(self):
        '''
        This function is temporary and must be replaced in functionality by
        getRedditListFromFile()

        This function returns a list of reddit information after call(s)
        to the reddit api
        returns:
            list of html-free tuples in the form of
                [
                    ('reddit title', 'description', 'id', 'url'),
                    ...
                ],
        '''
        reddit_base_url = 'https://www.reddit.com'
        subreddits = ['CoronavirusNewYork', 'coronavirus', 'legaladvice']
        all_reddit = []
        # Using public-facing Reddit's API, with its own search ranking engine.
        # (Not using PRAW, even with larger request size, though there are 'insignificant' rate limit.)
        # TODO: Will probably want to use Pushshift for historic data eventually.
        # headers = {'User-agent': 'redditRetrival'}, needed to uniquely identify to prevent rate limiting
        for subreddit in subreddits:
            r = requests.get('https://www.reddit.com/r/' + subreddit + '/search/.json?q=coronavirus&restrict_sr=1&limit=1000', headers={
                'User-agent': 'redditRetrival'})
            data = r.json()
            for sub in data['data']['children']:
                # TF-IDF ranking will eventually be performed on the feature vector of, title + body.
                # Currently, posts can be links (ONLY having a url), or a body (i.e. a selftext).
                # So submission.selftext could sometimes be empty (may need to filter?).
                submission = sub['data']
                all_reddit.append((submission['title'], "~Text~:" + submission['selftext'],
                               str(submission['id']), reddit_base_url + submission['permalink']))
        return all_reddit

    def getRedditListFromFile(self):
        '''
        This function returns a list of reddit information after scanning
        where the reddit data json is located (static jsons must be created first):
            list of html-free tuples in the form of
                [
                    ('reddit title', 'description', 'id', 'url'),
                    ...
                ],
        '''
        # TODO: take the reddit_file data, format it appropriately, and append it to ret, and return ret
        ret = []
        for filename in self.STATIC_DATA_PATH:
            reddit_file_path = os.path.join(self.DATA_ROOT, self.FOLDER_NAME, filename)
            reddit_file = json.load(open(reddit_file_path))
            # TODO
            for k, submission in enumerate(reddit_file):
                if 'selftext' not in submission:
                    continue
                ret.append((submission['title'], submission['selftext'], submission['id'], submission['full_link']))
        return ret

    def getRedditList(self):
        '''
        Middle-man function that returns the correct reddit list
        '''
        # TODO: replace with return self.getRedditListFromFile()
        return self.getRedditListFromFile()

    def getRedditDict(self):
        '''
        This function returns a dict of reddit information after scanning
        where the reddit data json is located (static jsons must be created first):
            dictionary of id, html-free tuples in the form of
                {
                    id: ('reddit title', 'description', 'id', 'url'),
                    ...
                },
        '''
        ret = {}
        for elem in self.reddit_list:
            ret[str(elem[2])] = (elem[0], elem[1], elem[2], elem[3])
        return ret
