import re
from flask import Flask, render_template, url_for, json
import json
from app.irsystem.models.helpers import *
import random
import requests
import os
import praw
import time
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from bs4 import BeautifulSoup

class StatuteData():
    def __init__(self):
        '''
        self.FOLDER_NAME: folder where all statute related json data is stored
        self.DATA_ROOT: Path to self.FOLDER_NAME
        self.STATIC_DATA_PATH: Entire path including where self.FOLDER_NAME is
        self.statute_list: List of statute results formatted as described in getStatuteListFromFile()
        self.statute_dict: Dict of statute results indexed on statute id
        self.ids_statutes_pair: Tuple of lists as identified in getCleanStatute(), utilized in tfidf
        '''
        self.FOLDER_NAME = 'statute_data'
        self.DATA_ROOT = os.path.realpath(os.path.dirname('app/data/' + self.FOLDER_NAME))
        self.STATIC_DATA_PATH = os.listdir(os.path.join(self.DATA_ROOT, self.FOLDER_NAME))
        self.temp_list = []
        self.cur_id = 0
        self.statute_list = self.getStatuteList()
        self.statute_dict = self.getStatuteDict()
        self.ids_statutes_pair = self.getCleanStatutes()

    def getCleanStatutes(self):
        '''
        Preprocesses statute results to extract and concat statute titles and body

        Parameters:
            self.statute_list:
                [
                    ('statute title', 'description', 'id', 'url'),
                    ...
                ],
        Returns:
            tuple of lists, where the first element is a list of statute IDs and
            the second element is an array where each element is the corresponding text
            (title and body text concatenated together) for that statute result.
        '''
        ret = ([], [])
        for elem in self.statute_list:
            text_str = cleanText(removeHTML(elem[0] + ' ' + elem[1]))
            ret[0].append(str(elem[2]))
            ret[1].append(text_str)
        return ret

    def getStatuteListFromFile(self):
        '''
        This function returns a list of statute information after scanning
        where the statute data json is located (static jsons must be created first):
            list of html-free tuples in the form of
                [
                    ('statute title', 'description', 'id', 'url'),
                    ...
                ],
        '''
        ret = []
        cur_id = 0
        for filename in self.STATIC_DATA_PATH:
            statute_file_path = os.path.join(self.DATA_ROOT, self.FOLDER_NAME, filename)
            statute_file = json.load(open(statute_file_path))
            orig = statute_file['result']
            cur_pos = statute_file['result']['documents']
            self.recurseJSON(cur_pos)
        return self.temp_list

    def recurseJSON(self, cur_pos):
        if isinstance(cur_pos, dict):
            if 'docType' in cur_pos and cur_pos['docType'] == 'SECTION':
                title = cur_pos['title']
                id = self.cur_id
                self.cur_id += 1
                content = cleanText(removeHTML(cur_pos['text']))
                self.temp_list.append((title, self.customClean(content), str(self.cur_id), 'TEXT'))
            elif 'items' in cur_pos:
                self.recurseJSON(cur_pos['items'])
            else:
                self.recurseJSON(cur_pos['documents'])
        elif isinstance(cur_pos, list):
            for i, elem in enumerate(cur_pos):
                self.recurseJSON(cur_pos[i])

    def customClean(self, s):
        res = re.sub(r'\\n', '\n', s)
        res = ' '.join(list(filter(lambda x : x != '', res.split(' '))))
        return res

    def getStatuteList(self):
        return self.getStatuteListFromFile()

    def getStatuteDict(self):
        '''
        This function returns a dict of statute information after scanning
        where the statute data json is located (static jsons must be created first):
            dictionary of id, html-free tuples in the form of
                {
                    id: ('statute title', 'description', 'id', 'url'),
                    ...
                },
        '''
        ret = {}
        for elem in self.statute_list:
            ret[str(elem[2])] = (elem[0], elem[1], elem[2], elem[3])
        return ret
