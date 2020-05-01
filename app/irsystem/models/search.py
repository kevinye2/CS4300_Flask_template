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

def plainFilter(doc_rankings, content_dict, reddit_range_utc=None):
    ret = []
    for idx, doc_id in enumerate(doc_rankings):
        content = content_dict[doc_id]
        if reddit_range_utc is None:
            ret.append((content[0], content[1][0:min(len(content[1]), 3000):1],
                doc_id, content[3]))
        elif content[4] >= reddit_range_utc[0] and content[4] <= reddit_range_utc[1]:
            ret.append((content[0], content[1][0:min(len(content[1]), 3000):1],
                doc_id, content[3]))
    return ret

def rocchioFilter(query, relevance_data, rocchio, rank_info, doc_rankings, content_dict, upper_limit, reddit_range_utc=None):
    if query in relevance_data:
        rocchio.addMultipleTraining(query, relevance_data[query])
        new_query = rocchio.produceNewQuery()
        rocchio.resetAll()
        new_doc_rankings = rank_info.getRankingsWithQueryVector(new_query, upper_limit)
        return plainFilter(new_doc_rankings, content_dict, reddit_range_utc)
    else:
        return plainFilter(doc_rankings, content_dict, reddit_range_utc)

def logRegFilter(query, relevance_data, log_reg, doc_rankings, content_dict, reddit_range_utc=None):
    log_reg.addMultipleTraining(relevance_data)
    predictions = log_reg.predictRelevance(query, doc_rankings)
    log_reg.resetAll()
    ret = []
    for idx, doc_id in enumerate(doc_rankings):
        content = content_dict[doc_id]
        if predictions[idx] == 1 and reddit_range_utc is None:
            ret.append((content[0], content[1][0:min(len(content[1]), 3000):1],
                doc_id, content[3]))
        elif predictions[idx] == 1 and not reddit_range_utc is None:
            if content[4] >= reddit_range_utc[0] and content[4] <= reddit_range_utc[1]:
                ret.append((content[0], content[1][0:min(len(content[1]), 3000):1],
                    doc_id, content[3]))
    return ret

def legalTipResp(query, upper_limit=100, reddit_range_utc=[0, 2 * (10**9)], ml_mode=0, relevance_feedbacks=None):
    '''
    parameters:
        query: string describing user legal help request for COVID-19
        upper_limit: maximum number of results to return per category
        reddit_range_utc: Time range to look for reddit posts
        ml_mode: 0 is no ML, 1 is Logistic Regression, 2 is Rocchio
        relevance_feedbacks: Dictionary of:
            {
                'codes_info': {

                }
            }
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
    reddit_doc_rankings = reddit_rank_info.getRankings(query, upper_limit)
    if relevance_feedbacks is None:
        ret_reddit = plainFilter(reddit_doc_rankings, reddit_dict, reddit_range_utc)
    elif ml_mode < 2:
        if ml_mode == 0:
            ret_reddit = plainFilter(reddit_doc_rankings, reddit_dict, reddit_range_utc)
        else:
            ret_reddit = logRegFilter(query,
                relevance_feedbacks['reddit_info'],
                reddit_log_reg,
                reddit_doc_rankings,
                reddit_dict,
                reddit_range_utc)
    else:
        ret_reddit = rocchioFilter(query,
            relevance_feedbacks['reddit_info'],
            reddit_rocchio,
            reddit_rank_info,
            reddit_doc_rankings,
            reddit_dict,
            upper_limit,
            reddit_range_utc)

    # Ranking for cases
    cases_doc_rankings = cases_rank_info.getRankings(query, upper_limit)
    if relevance_feedbacks is None:
        ret_cases = plainFilter(cases_doc_rankings, cases_dict)
    elif ml_mode < 2:
        if ml_mode == 0:
            ret_cases = plainFilter(cases_doc_rankings, cases_dict)
        else:
            ret_cases = logRegFilter(query,
                relevance_feedbacks['cases_info'],
                cases_log_reg,
                cases_doc_rankings,
                cases_dict)
    else:
        ret_cases = rocchioFilter(query,
            relevance_feedbacks['cases_info'],
            cases_rocchio,
            cases_rank_info,
            cases_doc_rankings,
            cases_dict,
            upper_limit)

    # Ranking for statutes
    statutes_doc_rankings = statutes_rank_info.getRankings(query, upper_limit)
    if relevance_feedbacks is None:
        ret_statutes = plainFilter(statutes_doc_rankings, statutes_dict)
    elif ml_mode < 2:
        if ml_mode == 0:
            ret_statutes = plainFilter(statutes_doc_rankings, statutes_dict)
        else:
            ret_statutes = logRegFilter(query,
                relevance_feedbacks['codes_info'],
                statutes_log_reg,
                statutes_doc_rankings,
                statutes_dict)
    else:
        ret_statutes = rocchioFilter(query,
            relevance_feedbacks['codes_info'],
            statutes_rocchio,
            statutes_rank_info,
            statutes_doc_rankings,
            statutes_dict,
            upper_limit)

    resp_object['legal_codes'] = ret_statutes
    resp_object['legal_cases'] = ret_cases
    resp_object['reddit_posts'] = ret_reddit
    resp_object['stop_words'] = {
        'statutes': statutes_rank_info.stop_words,
        'cases': cases_rank_info.stop_words,
        'reddit': reddit_rank_info.stop_words
    }
    return resp_object
