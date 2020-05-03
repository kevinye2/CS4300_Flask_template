import re
import json
from app.irsystem.models.helpers import *
import random
import os
import time

class StatuteData():
    def __init__(self):
        '''
        self.FOLDER_NAME: folder where all statute related json data is stored
        self.DATA_ROOT: Path to self.FOLDER_NAME
        self.STATIC_DATA_PATH: Entire path including where self.FOLDER_NAME is
        self.statute_dict: Dict of statutes indexed on statute id
        self.ids_statutes_pair: Tuple of lists as identified in getCleanstatutes(), utilized in tfidf
        '''
        self.FOLDER_NAME = 'statute_data'
        self.DATA_ROOT = os.path.realpath(os.path.dirname('app/data/' + self.FOLDER_NAME))
        self.STATIC_DATA_PATH = os.listdir(os.path.join(self.DATA_ROOT, self.FOLDER_NAME))
        self.statute_dict = self.getStatuteDict()
        self.ids_statutes_pair = self.getCleanStatutes()

    def getCleanStatutes(self):
        '''
        Preprocesses statutes to extract and concat statute titles and body

        Parameters:
            self.statute_dict:
            {
                id: ('statute title', 'description', 'id', 'url'),
                ...
            }
        Returns:
            tuple of lists, where the first element
            of is a list of statute IDs and the second element is an
            array where each element is the corresponding text
            (title and body text concatenated together) for that statute.
        '''
        ret = ([], [])
        for key in self.statute_dict:
            statute = self.statute_dict[key]
            text_str = cleanText(statute[0] + ' ' + statute[1])
            ret[0].append(key)
            ret[1].append(text_str)
        return ret

    def getStatuteDictFromFile(self):
        '''
        This function returns:
            {
                id: ('statute title', 'description', 'id', 'url'),
                ...
            }
        '''
        ret = {}
        for filename in self.STATIC_DATA_PATH:
            statute_file_path = os.path.join(self.DATA_ROOT, self.FOLDER_NAME, filename)
            statute_file = json.load(open(statute_file_path))
            for statute in statute_file:
                str_id = str(statute[2])
                ret[str_id] = (statute[0], statute[1], str_id, statute[3])
        return ret

    def getStatuteDict(self):
        '''
        Middle-man function that returns the correct statute dict
        '''
        return self.getStatuteDictFromFile()
