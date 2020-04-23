from flask import Flask, render_template, url_for, json
import json
from . import *
from app.irsystem.models.helpers import *
import random
import requests
import os
import praw
import time
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from app.irsystem.data_handlers.redditdata import RedditData
from app.irsystem.data_handlers.casedata import CaseData
from app.irsystem.data_handlers.statutedata import StatuteData

cases_data = CaseData()
statutes_data = StatuteData()
reddit_data = RedditData()

def tfidfVectorize(docs):
    '''
    Return tf-idf scores of docs

    Parameters:
        doc_ids: unique IDs to identify corresponding docs
        docs: list of strings, where each string is a complete document
    Returns:
        tuple of (TF-IDF matrix, list of feature names, idf array, and dictionary of feature indexes)
    '''
    tf = TfidfVectorizer(max_df=0.95)
    tfidf_matrix = tf.fit_transform(docs).toarray()
    feature_names = tf.get_feature_names()
    feature_idx_dict = {}
    for idx, elem in enumerate(feature_names):
        feature_idx_dict[elem] = idx
    return tfidf_matrix, feature_names, tf.idf_, feature_idx_dict

def getRankings(query, doc_ids, tfidf_matrix, feature_names, idf_array, feature_idx_dict, upper_limit):
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
    sorted_idx_ranked_res = np.flip(np.argsort(ranked_res))[0:upper_limit:1]
    for i, idx in enumerate(sorted_idx_ranked_res):
        ret.append(doc_ids[idx])
    return ret

def legalTipResp(query, county, upper_limit=100):
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
    resp_object = {}

    cases_dict = cases_data.case_dict
    cases_clean = cases_data.ids_cases_pair
    reddit_dict = reddit_data.reddit_dict
    reddit_clean = reddit_data.ids_reddit_pair
    statutes_dict = statutes_data.statute_dict
    statutes_clean = statutes_data.ids_statutes_pair

    # Getting TF-IDF matrices for reddit
    reddit_tfidf, reddit_feat, reddit_idf, reddit_idx_dict = tfidfVectorize(reddit_clean[1])
    reddit_rankings = getRankings(query,
        reddit_clean[0], reddit_tfidf, reddit_feat, reddit_idf, reddit_idx_dict, upper_limit)
    ret_reddit = []
    for doc_id in reddit_rankings:
        content = reddit_dict[doc_id]
        ret_reddit.append((content[0], content[1], doc_id, content[3]))

    # Getting TF-IDF matrices for cases
    cases_tfidf, cases_feat, cases_idf, cases_idx_dict = tfidfVectorize(cases_clean[1])
    cases_rankings = getRankings(query,
        cases_clean[0], cases_tfidf, cases_feat, cases_idf, cases_idx_dict, upper_limit)
    ret_cases = []
    for doc_id in cases_rankings:
        content = cases_dict[doc_id]
        ret_cases.append((content[0], content[1], doc_id, content[3]))

    # Getting TF-IDF matrices for statutes
    statutes_tfidf, statutes_feat, statutes_idf, statutes_idx_dict = tfidfVectorize(statutes_clean[1])
    statutes_rankings = getRankings(query,
        statutes_clean[0], statutes_tfidf, statutes_feat, statutes_idf, statutes_idx_dict, upper_limit)
    ret_statutes = []
    for doc_id in statutes_rankings:
        content = statutes_dict[doc_id]
        ret_statutes.append((content[0], content[1], doc_id, content[3]))

    resp_object['legal_codes'] = ret_statutes
    resp_object['legal_cases'] = ret_cases
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
