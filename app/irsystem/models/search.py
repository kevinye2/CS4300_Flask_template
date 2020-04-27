from flask import Flask, render_template, url_for, json
import json
from . import *
from app.irsystem.models.helpers import *
import random
import requests
import os
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from app.irsystem.data_handlers.redditdata import RedditData
from app.irsystem.data_handlers.casedata import CaseData
from app.irsystem.data_handlers.statutedata import StatuteData
from app.irsystem.ranking_handlers.tfidffunc import TFIDFHolder
from app.irsystem.ranking_handlers.logreg import LogReg

cases_data = CaseData()
statutes_data = StatuteData()
reddit_data = RedditData()
cases_rank_info = TFIDFHolder(cases_data.ids_cases_pair)
statutes_rank_info = TFIDFHolder(statutes_data.ids_statutes_pair)
reddit_rank_info = TFIDFHolder(reddit_data.ids_reddit_pair)
cases_log_reg = LogReg(cases_rank_info,
    os.path.realpath('app/data/ml_data/case_log_reg.npz'),
    os.path.realpath('app/data/ml_data/case_label.npz'))
statutes_log_reg = LogReg(statutes_rank_info,
    os.path.realpath('app/data/ml_data/statute_log_reg.npz'),
    os.path.realpath('app/data/ml_data/statute_log_reg.npz'))
reddit_log_reg = LogReg(reddit_rank_info,
    os.path.realpath('app/data/ml_data/reddit_log_reg.npz'),
    os.path.realpath('app/data/ml_data/reddit_log_reg.npz'))

def legalTipResp(query, upper_limit=100):
    '''
    parameters:
        query: string describing user legal help request for COVID-19
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
    reddit_dict = reddit_data.reddit_dict
    statutes_dict = statutes_data.statute_dict

    # Getting TF-IDF matrices for reddit
    reddit_rankings = reddit_rank_info.getRankings(query)
    ret_reddit = []
    for doc_id in reddit_rankings:
        content = reddit_dict[doc_id]
        ret_reddit.append((content[0], content[1], doc_id, content[3]))

    # Getting TF-IDF matrices for cases
    cases_rankings = cases_rank_info.getRankings(query)
    ret_cases = []
    for doc_id in cases_rankings:
        content = cases_dict[doc_id]
        ret_cases.append((content[0], content[1][0:min(len(content[1]), 1500):1],
            doc_id, content[3]))

    # Getting TF-IDF matrices for statutes
    statutes_rankings = statutes_rank_info.getRankings(query)
    ret_statutes = []
    for doc_id in statutes_rankings:
        content = statutes_dict[doc_id]
        ret_statutes.append((content[0], content[1], doc_id, content[3]))

    resp_object['legal_codes'] = ret_statutes
    resp_object['legal_cases'] = ret_cases
    resp_object['reddit_posts'] = ret_reddit
    return resp_object

def feedbackRatings(query, relevant_doc_id):
    '''
    parameters:
        query: original string query
        relevant_doc_id: a [category, doc_id, ranking, is_relevant] 4 element list (basically a tuple)
        that indicates whether doc_id in category is relevant to query;
        ranking is the original ranking provided by the system for the
        document in regards to its category (statutes, cases, reddit posts) and
        is an integer 1...n
    '''
    category = relevant_doc_id[0]
    doc_id = relevant_doc_id[1]
    label = 1 if relevant_doc_id[3] else -1
    if category == 'cases_info':
        cases_log_reg.addTraining(query, doc_id, label)
    elif category == 'codes_info':
        statutes_log_reg.addTraining(query, doc_id, label)
    else:
        reddit_log_reg.addTraining(query, doc_id, label)
