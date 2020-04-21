from . import *
from app.irsystem.models.helpers import *
import random
import string
import requests
import os
import praw
import time
import pprint
import pandas as pd
import numpy as np
import string
from scipy.sparse.csr import csr_matrix
from sklearn.feature_extraction.text import TfidfTransformer, TfidfVectorizer
from sklearn.feature_extraction.text import CountVectorizer
from bs4 import BeautifulSoup
import re

def getCases(query, county):
    '''
    parameters:
        query: string describing user legal help request for COVID-19
        county: string describing which county the user is in
    returns:
        list of tuples in the form of
            [
                ('Statute title', 'description', id, url),
                ...
            ],
    '''
    ###does not filter by county yet###
    r = requests.get('https://api.case.law/v1/cases/?search=' +
                     query + '&jurisdiction=ny&full_case=true&body_format=html')
    data = r.json()
    all_cases = []
    for case in data['results']:
        preview = '\n'.join(case['preview'])
        all_cases.append(
            (case['name'], preview, case['id'], case['frontend_url']))
    return all_cases


def getReddit(query, county):
    '''
    parameters:
        query: string describing user legal help request for COVID-19
        county: string describing which county the user is in
    returns:
        list of tuples in the form of
            [
                ('Reddit article title', 'text body', id, url),
                ...
            ],
    '''
    start_time = time.time()
    ###does not filter by county yet###
    reddit_base_url = 'https://www.reddit.com'
    subreddits = ['CoronavirusNewYork', 'coronavirus', 'legaladvice']
    # Using public-facing Reddit's API, with its own search ranking engine.
    # (Not using PRAW, even with larger request size, though there are 'insignificant' rate limit.)
    # TODO: Will probably want to use Pushshift for historic data eventually.
    # headers = {'User-agent': 'redditRetrival'}, needed to uniquely identify to prevent rate limiting
    r = requests.get('https://www.reddit.com/r/' + subreddits[2] + '/search/.json?q=' + query + '&restrict_sr=1&limit=1000', headers={
                     'User-agent': 'redditRetrival'})  # limit should be 100 anyway
    data = r.json()
    # pprint.pprint(data)
    all_reddit = []
    for sub in data['data']['children']:
        # TF-IDF ranking will eventually be performed on the feature vector of, title + body.
        # Currently, posts can be links (ONLY having a url), or a body (i.e. a selftext). So submission.selftext could sometimes be empty (may need to filter?).
        # pprint.pprint(sub)
        # print(type(sub))
        submission = sub['data']
        all_reddit.append((submission['title'], "~Text~:" + submission['selftext'],
                           submission['id'], reddit_base_url + submission['permalink']))
    end_time = time.time()
    print('Finished pulling from Reddit API')
    print("took {:.4f}s".format(end_time - start_time))
    return all_reddit


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
    s = re.sub(r'[^ 0-9a-z]', '', s)
    s = ' '.join([word for word in s.split() if len(word) > 2])
    return s


def cleanCases(legal_cases):
    '''
    Preprocesses legal cases to extract and concat case titles and body

    Parameters:
        legal_cases: list of tuples of legal cases from Case Law API:
            list of tuples in the form of
                [
                    ('Statute title', 'description', id, url),
                    ...
                ],
    Returns:
        tuple of lists, where the first element is a list of case IDs and
        the second element is an array where each element is the corresponding text
        (title and body text concatenated together) for that case.
    '''
    ret = ([], [])
    for elem in legal_cases:
        html_str = BeautifulSoup(elem[0] + ' ' + elem[1])
        text_str = cleanText(html_str.get_text())
        ret[0].append(elem[2])
        ret[1].append(text_str)
    return ret


def cleanRedditPosts(reddit_posts):
    '''
    Preprocesses reddit posts to extract and concat case titles and body

    Parameters:
        reddit_posts: list of tuples of reddit posts
    Returns:
        tuple where the first element is an array of post IDs and the
        second element is an array where each element is the corresponding text
        (title and body text concatenated together) for that reddit post.
    '''
    post_ids = []
    post_data = []  # 1-to-1 correspondence in post_ids
    for post in reddit_posts:
        title = post[0]
        text = post[1]
        id_ = post[2]
        title = cleanText(title)
        text = cleanText(text)
        post_data.append(title+' '+text)
        post_ids.append(id_)

    return (post_ids, post_data)


def getTfidfScores(doc_ids, docs):
    '''
    Computes Tf-idf scores for given docs.

    Parameters:
        doc_ids: unique IDs to identify corresponding docs
        docs: list of strings, where each string is a complete document
    Returns:
        tuple of (TF-IDF matrix, list of feature names)
    '''
    tf = TfidfVectorizer()
    tfidf_matrix = tf.fit_transform(docs)
    feature_names = tf.get_feature_names()
    # cv = CountVectorizer()
    # word_counts = cv.fit_transform(docs)

    # transformer = TfidfTransformer()
    # transformer.fit(word_counts)

    # sparse_word_counts = cv.transform(docs)
    # tfidf_scores = transformer.transform(sparse_word_counts)
    # feature_names = cv.get_feature_names()

    return (tfidf_matrix, feature_names)


def tfidfVectorize(doc_ids, docs):
    '''
    Wrapper function that returns a tuple of tfidf scores and features names
    by calling getTfidfScores
    TODO: possibly more analysis logic in here

    Parameters:
        doc_ids: unique IDs to identify corresponding docs
        docs: list of strings, where each string is a complete document
    Returns:
        tuple of (TF-IDF matrix, list of feature names)
    '''
    # docs = ["the house had a tiny little mouse",
    #         "the cat saw the mouse",
    #         "the mouse ran away from the house",
    #         "the cat finally ate the mouse",
    #         "the end of the mouse story"
    #         ]
    tfidf_matrix, feature_names = getTfidfScores(doc_ids, docs)
    # doc = 0
    # feature_index = tfidf_matrix[doc, :].nonzero()[1]
    # tfidf_scores = zip(
    #     feature_index, [tfidf_matrix[doc, x] for x in feature_index])
    # for w, s in [(feature_names[i], s) for (i, s) in tfidf_scores]:
    #     print(w, s)
    # return (tfidf_scores, feature_names)
    return (tfidf_matrix, feature_names)


def getCossim(query, tfidf_matrix):
    '''
    Compute cosine similarity between the query and corpus of docs represented
    by the TF-IDF matrix.

    parameters:
        query: string representing user's query
        doc_index: index of the document in TF-IDF matrix with which to compute
        cosine similarity
        tfidf_matrix: TF-IDF matrix where each row corresponds to a document
    returns:

    '''
    raise NotImplemented()


def getRanking(query, tfidf_matrix, doc_ids, corpus):
    '''
    Generates a ranking based on cosine similarity of the query and corpus of
    documents from one of {reddit posts, cases, laws}.

    parameters:
        query: string representing user's query
        tfidf_matrix: TF-IDF matrix where each row corresponds to a document
        doc_ids: IDs of documents with 1-to-1 correspondence to the rows in
        tfidf_matrix
        corpus: string indicator of which corpus we are ranking. Has to be
        one of 'reddit'/'cases'/'laws'
    returns:
        Sorted (ranked) list of tuples where each tuple is (rank, doc_id)
    '''
    getCossim()
    raise NotImplemented()


def legalTipResp(query, county):
    '''
    parameters:
        query: string describing user legal help request for COVID-19
        county: string describing which county the user is in
    returns:
        dictionary in the form of
            {'legal_codes' : [
                ('Statute title', 'description', id, url),
                ...
                ],
            'legal_cases' : [
                ('Case title', 'description', id, url),
                ...
                ],
            'reddit_posts' : [
                ('Reddit title', 'description', id, url),
                ...
                ]
            }
        id represents the unique string identifier for the document, no spaces
        (all documents must have unique id regardless of whether it is a statute,
        case, or reddit post)
        url represents the relevant url for the document

        All results should be ranked in the list, where the most relevant occurs
        first
    '''
    ###Follow the template; replace this code###
    resp_object = {}
    temp = []
    total_string = string.ascii_lowercase + string.ascii_uppercase + string.digits
    for i in range(107):
        temp_title = ''
        temp_content = ''
        for j in range(100):
            for k in range(random.choice(range(1, 21))):
                if j < 20:
                    temp_title += random.choice(total_string)
                temp_content += random.choice(total_string)
            temp_title += ' '
            temp_content += ' '
        temp.append((
            str(i) + temp_title + str(i),
            str(i) + temp_content + str(i),
            'code_' + str(i*i),
            'https://legislation.nysenate.gov/static/docs/html/index.html#'))
    resp_object['legal_codes'] = temp
    # temp = []
    # for i in range(94):
    #     temp_title = ''
    #     temp_content = ''
    #     for j in range(100):
    #         for k in range(random.choice(range(1, 21))):
    #             if j < 20:
    #                 temp_title += random.choice(total_string)
    #             temp_content += random.choice(total_string)
    #         temp_title += ' '
    #         temp_content += ' '
    #     temp.append((
    #         str(i) + temp_title + str(i),
    #         str(i) + temp_content + str(i),
    #         'case_' + str(i*i),
    #         'https://case.law/'))
    # resp_object['legal_cases'] = temp

    ###getting Caselaw data from API using helper function getCases()###
    legal_cases = getCases(query, county)
    reddit_posts = getReddit(query, county)

    # Cleaning the data returned by APIs
    # legal_cases_clean = cleanCases(legal_cases)
    reddit_posts_clean = cleanRedditPosts(reddit_posts)

    # Getting TF-IDF matrices
    reddit_tfidf = tfidfVectorize(reddit_posts_clean[0], reddit_posts_clean[1])
    tfidf_scores_by_category = {'reddit_posts': reddit_tfidf}

    # TODO: query expansion using Rocchio

    # Getting a ranking based on cosine similarity
    # reddit_ranking = getRanking()

    # Generating response
    resp_object['legal_cases'] = legal_cases
    resp_object['reddit_posts'] = reddit_posts

    return resp_object


def feedbackRatings(query, county, relevant_doc_id):
    '''
    parameters:
        query: original string query
        county: original county selection
        relevant_doc_id: a [doc_id, ranking] 2 element list (basically a tuple)
        deeemed relevant to query and county;
        ranking is the original ranking provided by the system for the
        document in regards to its category (statutes, cases, reddit posts) and
        is an integer 1...n
    '''
    ###Perform analysis on the relevancy rating###
    return {'Great 1': relevant_doc_id[0], 'Great 2': relevant_doc_id[1]}
