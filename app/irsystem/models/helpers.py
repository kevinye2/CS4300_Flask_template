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
