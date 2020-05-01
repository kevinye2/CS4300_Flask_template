from . import *
from app.irsystem.models.helpers import *
import os
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from app.irsystem.data_handlers.redditdata import RedditData
from app.irsystem.data_handlers.casedata import CaseData
from app.irsystem.data_handlers.statutedata import StatuteData
from app.irsystem.ranking_handlers.tfidffunc import TFIDFHolder
from app.irsystem.ranking_handlers.logreg import LogReg
from app.irsystem.ranking_handlers.rocchio import Rocchio

'''
try:
    requests.get('https://legal-pro-tips-wait.herokuapp.com')
except Exception:
    pass
'''
cases_data = CaseData()
statutes_data = StatuteData()
reddit_data = RedditData()
cases_rank_info = TFIDFHolder(cases_data.ids_cases_pair)
statutes_rank_info = TFIDFHolder(statutes_data.ids_statutes_pair)
reddit_rank_info = TFIDFHolder(reddit_data.ids_reddit_pair)
cases_log_reg = LogReg(cases_rank_info)
statutes_log_reg = LogReg(statutes_rank_info)
reddit_log_reg = LogReg(reddit_rank_info)
cases_rocchio = Rocchio(cases_rank_info)
statutes_rocchio = Rocchio(statutes_rank_info)
reddit_rocchio = Rocchio(reddit_rank_info)

def rankingFilter(reg_model, doc_rankings, query, content_dict, pass_through=False, reddit_range_utc=None):
    ret = []
    relevant_docs = reg_model.predictRelevance(query, doc_rankings, pass_through)
    for idx, doc_id in enumerate(doc_rankings):
        content = content_dict[doc_id]
        if relevant_docs[idx] == 1 and reddit_range_utc is None:
            ret.append((content[0], content[1][0:min(len(content[1]), 3000):1],
                doc_id, content[3]))
        elif relevant_docs[idx] == 1 and not reddit_range_utc is None:
            if content[4] >= reddit_range_utc[0] and content[4] <= reddit_range_utc[1]:
                ret.append((content[0], content[1][0:min(len(content[1]), 3000):1],
                    doc_id, content[3]))
    return ret

def legalTipResp(query, upper_limit=100, reddit_range_utc=[0, 2 * (10**9)], ml_mode=0):
    '''
    parameters:
        query: string describing user legal help request for COVID-19
        upper_limit: maximum number of results to return per category
        reddit_range_utc: Time range to look for reddit posts
        ml_mode: 0 is no ML, 1 is Logistic Regression, 2 is Rocchio
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
    upper_limit = min(upper_limit, 100)
    resp_object = {}

    cases_dict = cases_data.case_dict
    reddit_dict = reddit_data.reddit_dict
    statutes_dict = statutes_data.statute_dict

    # Ranking for reddit
    if ml_mode < 2 or reddit_rocchio.new_query is None:
        pass_through = True if ml_mode == 0 else False
        ret_reddit = rankingFilter(reddit_log_reg,
            reddit_rank_info.getRankings(query, upper_limit),
            query,
            reddit_dict,
            pass_through,
            reddit_range_utc)
    else:
        pass_through = True
        ret_reddit = rankingFilter(reddit_log_reg,
            reddit_rank_info.getRankingsWithQueryVector(reddit_rocchio.new_query, upper_limit),
            query,
            reddit_dict,
            pass_through,
            reddit_range_utc)


    # Ranking for cases
    if ml_mode < 2 or cases_rocchio.new_query is None:
        pass_through = True if ml_mode == 0 else False
        ret_cases = rankingFilter(cases_log_reg,
            cases_rank_info.getRankings(query, upper_limit),
            query,
            cases_dict,
            pass_through)
    else:
        pass_through = True
        ret_cases = rankingFilter(cases_log_reg,
            cases_rank_info.getRankingsWithQueryVector(cases_rocchio.new_query, upper_limit),
            query,
            cases_dict,
            pass_through)

    # Ranking for statutes
    if ml_mode < 2 or statutes_rocchio.new_query is None:
        pass_through = True if ml_mode == 0 else False
        ret_statutes = rankingFilter(statutes_log_reg,
            statutes_rank_info.getRankings(query, upper_limit),
            query,
            statutes_dict,
            pass_through)
    else:
        pass_through = True
        ret_statutes = rankingFilter(statutes_log_reg,
            statutes_rank_info.getRankingsWithQueryVector(statutes_rocchio.new_query, upper_limit),
            query,
            statutes_dict,
            pass_through)

    resp_object['legal_codes'] = ret_statutes
    resp_object['legal_cases'] = ret_cases
    resp_object['reddit_posts'] = ret_reddit
    resp_object['stop_words'] = {
        'statutes': statutes_rank_info.stop_words,
        'cases': cases_rank_info.stop_words,
        'reddit': reddit_rank_info.stop_words
    }
    return resp_object

def feedbackRatings(query, relevant_doc_id, ml_mode=0):
    '''
    parameters:
        query: original string query
        relevant_doc_id: a [category, doc_id, ranking, is_relevant] 4 element list (basically a tuple)
        that indicates whether doc_id in category is relevant to query;
        ranking is the original ranking provided by the system for the
        document in regards to its category (statutes, cases, reddit posts) and
        is an integer 1...n
        ml_mode: 0 is no ML, 1 is Logistic Regression, 2 is Rocchio
    '''
    if ml_mode == 0:
        return 200
    category = relevant_doc_id[0]
    doc_id = relevant_doc_id[1]
    label = 1 if relevant_doc_id[3] else -1
    if ml_mode == 1:
        if category == 'cases_info':
            resp_code = cases_log_reg.addTraining(query, doc_id, label)
        elif category == 'codes_info':
            resp_code = statutes_log_reg.addTraining(query, doc_id, label)
        else:
            resp_code = reddit_log_reg.addTraining(query, doc_id, label)
        return resp_code
    elif ml_mode == 2:
        if category == 'cases_info':
            resp_code = cases_rocchio.addTraining(query, doc_id, label)
        elif category == 'codes_info':
            resp_code = statutes_rocchio.addTraining(query, doc_id, label)
        else:
            resp_code = reddit_rocchio.addTraining(query, doc_id, label)
        return resp_code
    return 400
