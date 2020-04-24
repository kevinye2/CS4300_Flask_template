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

cases_data = CaseData()
statutes_data = StatuteData()
reddit_data = RedditData()
cases_rank_info = TFIDFHolder(cases_data.ids_cases_pair)
statutes_rank_info = TFIDFHolder(statutes_data.ids_statutes_pair)
reddit_rank_info = TFIDFHolder(reddit_data.ids_reddit_pair)

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
        ret_cases.append((content[0], content[1], doc_id, content[3]))

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
