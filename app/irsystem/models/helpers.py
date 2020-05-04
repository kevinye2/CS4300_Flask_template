import re
from bs4 import BeautifulSoup

def cleanText(s):
    '''
    Standard text cleaning and preprocessing:
    - lowercases
    - takes out punctuation and apostrophes
    - removes words that have 2 characters or fewer

    Parameters:
        s: string that represents the text to be processed
    Returns:
        processed string s
    '''
    s = s.lower()
    s = re.sub(r'[^ 0-9a-z]', ' ', s)
    s = ' '.join([word for word in s.split() if len(word) > 2])
    return s

def removeHTML(s):
    '''
    Remove all HTML tags and related elements from s; return cleaned string
    '''
    html_str = BeautifulSoup(s, features='html.parser')
    return html_str.get_text()

def checkQueryInvalid(query):
    return not isinstance(query, str) or query == ''

def checkMaxResInvalid(max_res):
    return not isinstance(max_res, int) or (max_res < 5 or max_res > 100)

def checkMlModeInvalid(ml_mode):
    return not isinstance(ml_mode, int) or (ml_mode < 0 or ml_mode > 2)

def checkRedditRangeInvalid(reddit_range_utc):
    return not isinstance(reddit_range_utc, list) or (len(reddit_range_utc) != 2 or \
        (not isinstance(reddit_range_utc[0], int) or not isinstance(reddit_range_utc[1], int)))
