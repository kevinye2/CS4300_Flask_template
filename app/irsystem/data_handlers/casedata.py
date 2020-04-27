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

class CaseData():
    def __init__(self):
        '''
        self.FOLDER_NAME: folder where all case related json data is stored
        self.DATA_ROOT: Path to self.FOLDER_NAME
        self.STATIC_DATA_PATH: Entire path including where self.FOLDER_NAME is
        self.case_list: List of cases formatted as described in getCaseListFromFile()
        self.case_dict: Dict of cases indexed on case id
        self.ids_cases_pair: Tuple of lists as identified in getCleanCases(), utilized in tfidf
        '''
        self.FOLDER_NAME = 'case_data'
        self.DATA_ROOT = os.path.realpath(os.path.dirname('app/data/' + self.FOLDER_NAME))
        self.STATIC_DATA_PATH = os.listdir(os.path.join(self.DATA_ROOT, self.FOLDER_NAME))
        self.case_list = self.getCaseList()
        self.case_dict = self.getCaseDict()
        self.ids_cases_pair = self.getCleanCases()

    def getCleanCases(self):
        '''
        Preprocesses legal cases to extract and concat case titles and body

        Parameters:
            self.case_list:
            [
                ('case title', 'description', 'id', 'url'),
                ...
            ]
        Returns:
            dictionary tuple of lists indexed on county, where the first element
            of an entry list is a list of case IDs and the second element is an
            array where each element is the corresponding text
            (title and body text concatenated together) for that case.
        '''
        ret = ([], [])
        for elem in self.case_list:
            text_str = cleanText(removeHTML(elem[0] + ' ' + elem[2]))
            ret[0].append(str(elem[1]))
            ret[1].append(text_str)
        return ret

    def getCaseListFromFile(self):
        '''
        This function returns:
        [
            ('case title', 'id', 'description', 'id'),
            ...
        ]
        '''
        ret = []
        for filename in self.STATIC_DATA_PATH:
            case_file_path = os.path.join(self.DATA_ROOT, self.FOLDER_NAME, filename)
            if '.json' in filename:
                case_file = json.load(open(case_file_path))
                for elem in case_file:
                    ret.append((elem[0], elem[1],
                        elem[2][0:min(1500, len(elem[2]))], elem[3]))
        return ret

    def getCaseList(self):
        '''
        Middle-man function that returns the correct case list
        '''
        return self.getCaseListFromFile()

    def getCaseDict(self):
        '''
        This function returns:
            {
                id: ('case title', 'description', 'id', 'url'),
                ...
            }
        '''
        ret = {}
        for elem in self.case_list:
            ret[str(elem[1])] = (elem[0], elem[2], elem[1], elem[3])
        return ret
