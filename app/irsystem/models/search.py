import re
from collections import defaultdict, Counter
from flask import Flask, render_template, url_for, json
import json
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
from collections import defaultdict, Counter


def getCases(query, county):
    '''
    parameters:
        query: string describing user legal help request for COVID-19
        county: string describing which county the user is in
    returns:
        list of tuples in the form of
            [
                ('case title', 'description', id, url),
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
        and dictionary of reddit content
            {
            'id': ('Reddit article title', 'text body', url)
            ...
            }
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
    reddit_dict = {}
    for sub in data['data']['children']:
        # TF-IDF ranking will eventually be performed on the feature vector of, title + body.
        # Currently, posts can be links (ONLY having a url), or a body (i.e. a selftext). So submission.selftext could sometimes be empty (may need to filter?).
        # pprint.pprint(sub)
        # print(type(sub))
        submission = sub['data']
        all_reddit.append((submission['title'], "~Text~:" + submission['selftext'],
                           submission['id'], reddit_base_url + submission['permalink']))
        reddit_dict[submission['id']] = (submission['title'], "~Text~:" + submission['selftext'],
                            reddit_base_url + submission['permalink'])
    end_time = time.time()
    print('Finished pulling from Reddit API')
    print("took {:.4f}s".format(end_time - start_time))
    return all_reddit, reddit_dict


def getLegalCodes():
    '''
    returns a list of static, raw json files taken from static data/ folder

    parameters:
        n/a
    returns:
        list of dictionaries (json files)
    '''
    DATA_ROOT = os.path.realpath(os.path.dirname('app/data'))
    static_data_path = os.listdir(os.path.join(DATA_ROOT, 'data'))
    data = []
    for filename in static_data_path:
        law_file_path = os.path.join(DATA_ROOT, 'data', filename)
        law_file = json.load(open(law_file_path))
        data.append(law_file)

    # print(data[0]['result'])
    return data


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
    s.translate(str.maketrans('', '', string.punctuation))
    s = ' '.join([word for word in s.split() if len(word) > 2])
    s = s.replace("'", "")
    s = s.replace("\\n", "")
    return s

def alphanumericOnly(s):
    '''
    Only keep alphanumeric and regular space in s

    Parameters:
        s: string that represents the text to be processed
    Returns:
        processed string s
    '''
    s = s.lower()
    s = re.sub(r'[^ #.0-9a-z]', ' ', s)
    s = ' '.join([word for word in s.split() if len(word) > 2])
    return s

def cleanLaws(laws):
    '''
    Preprocess laws to extract and concat law titles and body

    Parameters:
        laws: list of dictionaries, where each dictionary represents a static
            json file extracted from the static data/ folder
    Returns:
        tuple of lists, where the first element is a list of law IDs and the
        second element is an array where each element is the corresponding text
        (title and body text concatenated together) for that law.
    '''
    law_ids = []
    cleaned_laws = []
    title = laws[0]['result']['documents']['title']
    # print(laws[0]['result']['documents']['title'])
    for law in laws:
        title = law['result']['documents']['title']
        title = cleanText(title)
        law_type = law['result']['documents']['lawName']
        law_type = cleanText(law_type)

        law_text = ''
        items_path = law['result']['documents']['documents']['items']
        for item in items_path:
            item_text = item['text']
            item_text = cleanText(item_text)
            law_text += item_text + ' '
        full_law_text_feature = title + ' ' + law_type + ' ' + law_text
        law_ids.append(law['result']['info']['lawId'])
        cleaned_laws.append(full_law_text_feature)

    return (law_ids, cleaned_laws)


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

def tfidfVectorize(doc_ids, docs):
    '''
    Return tf-idf scores of docs

    Parameters:
        doc_ids: unique IDs to identify corresponding docs
        docs: list of strings, where each string is a complete document
    Returns:
        tuple of (TF-IDF matrix, list of feature names, idf array, and dictionary of feature indexes)
    '''
    tf = TfidfVectorizer(max_df=0.9, min_df=0.01)
    tfidf_matrix = tf.fit_transform(docs).toarray()
    feature_names = tf.get_feature_names()
    feature_idx_dict = {}
    for idx, elem in enumerate(feature_names):
        feature_idx_dict[elem] = idx
    return tfidf_matrix, feature_names, tf.idf_, feature_idx_dict

def getRankings(query, doc_ids, tfidf_matrix, feature_names, idf_array, feature_idx_dict):
    '''
    Compute resulting ranking cosine similarity between the query and corpus of docs represented
    by the TF-IDF matrix.

    parameters:
        query: string representing user's query
        doc_ids: List of doc_ids, ordered congruently to the corresponding
        rows of tfidf_matrix
        tfidf_matrix: TF-IDF matrix where each row corresponds to a document
        feature_names: List of all tokens, indexed corresponding to the columns
        of tfidf_matrix
        idf_array: List of all idf values, indexed per corresponding query index
        feature_idx_dict: Dictionary of key: query, value: corresponding index
        in idf_array and feature_names
    returns:
        Sorted (ranked) list of doc_id, most relevant first
    '''
    query_tok_tfidf = {}
    query_split = query.split()
    query_idxs = []
    ret = []
    # Counting the frequency for valid query tokens
    for tok in query_split:
        if not tok in feature_idx_dict:
            continue
        elif tok in query_tok_tfidf:
            query_tok_tfidf[tok] += 1
        else:
            query_tok_tfidf[tok] = 1
    # Multiplying term frequencies by idf
    for tok in query_tok_tfidf:
        idx = feature_idx_dict[tok]
        idf_val = idf_array[idx]
        query_idxs.append(idx)
        query_tok_tfidf[tok] *= idf_val
    query_idxs.sort()
    query_tfidf_vec = np.zeros(len(query_idxs))
    truncated_tfidf_mat = np.take(tfidf_matrix, query_idxs, axis=-1)
    for i in range(len(query_tfidf_vec)):
        feature = feature_names[query_idxs[i]]
        query_tfidf_vec[i] = query_tok_tfidf[feature]
    query_tfidf_vec /= np.sqrt(np.sum(query_tfidf_vec ** 2))
    ranked_res = np.sum(np.multiply(query_tfidf_vec, truncated_tfidf_mat),
        axis=-1)
    sorted_idx_ranked_res = np.flip(np.argsort(ranked_res))
    for i, idx in enumerate(sorted_idx_ranked_res):
        ret.append(doc_ids[idx])
    return ret

def buildInvertedIndex(laws):
    '''
    '''
    inv_index = defaultdict(list)
    for idx, law in enumerate(laws):
        for token in law.split():
            token = token.lower()
            inv_index[token].append(idx)
    return inv_index


def booleanSearch(query, county, laws):
    '''
    Version of boolean search that ranks items based on raw number of
    token correspondences in query and docs.
    '''
    query = cleanText(query)
    query = query + ' ' + county
    inverted_index = buildInvertedIndex(laws)
    docs_with_query_word = []
    for query_word in query:
        docs_with_query_word += [doc_id for doc_id,
                                 _ in enumerate(inverted_index[query_word])]

    doc_corr_counts = Counter(docs_with_query_word)
    ranking = [item[0] for item in doc_corr_counts.most_common(3)]

    return ranking


def formatLawsRanking(ranking, laws, law_ids):
    '''
    '''
    result = []
    for item in ranking:
        temp = []
        temp.append(law_ids[item])  # title
        temp.append(laws[item])  # content
        temp.append(item)  # id
        temp.append('static json file')  # url
        result.append(temp)
    return result


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

    ###getting Caselaw data from API using helper function getCases()###
    legal_cases = getCases(query, county)
    reddit_posts, reddit_dict = getReddit(query, county)
    laws = getLegalCodes()

    # Cleaning the data returned by APIs
    # legal_cases_clean = cleanCases(legal_cases)
    reddit_posts_clean = cleanRedditPosts(reddit_posts)
    laws = cleanLaws(laws)

    # Brute force boolean search on laws
    ranked_laws = booleanSearch(query, county, laws[1])
    ranked_laws = formatLawsRanking(ranked_laws, laws[1], laws[0])

    # Getting TF-IDF matrices
    reddit_tfidf, reddit_feat, reddit_idf, reddit_idx_dict = tfidfVectorize(reddit_posts_clean[0],
        map(lambda x: alphanumericOnly(x), reddit_posts_clean[1]))
    tfidf_scores_by_category = {'reddit_posts': reddit_tfidf}
    reddit_rankings = getRankings(query,
        reddit_posts_clean[0], reddit_tfidf, reddit_feat, reddit_idf, reddit_idx_dict)
    ret_reddit = []
    for doc_id in reddit_rankings:
        content = reddit_dict[doc_id]
        ret_reddit.append((content[0], content[1], doc_id, content[2]))

    # TODO: query expansion using Rocchio

    # Getting a ranking based on cosine similarity
    # reddit_ranking = getRanking()

    # Generating response
    resp_object['legal_codes'] = ranked_laws
    resp_object['legal_cases'] = legal_cases
    resp_object['reddit_posts'] = ret_reddit

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
