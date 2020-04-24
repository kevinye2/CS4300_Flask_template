from flask import Flask, render_template, url_for, json
from app.irsystem.models.helpers import *
import random
import requests
import os
import praw
import time
import numpy as np
from scipy import sparse
from sklearn.metrics.pairwise import linear_kernel
from sklearn.feature_extraction.text import TfidfVectorizer
from app.irsystem.data_handlers.redditdata import RedditData
from app.irsystem.data_handlers.casedata import CaseData
from app.irsystem.data_handlers.statutedata import StatuteData

class TFIDFHolder():
    def __init__(self, clean_data):
        self.clean_data = clean_data
        temp = self.tfidfVectorize(self.clean_data[1])
        self.tfidf = temp[0]
        self.feat = temp[1]
        self.idf = temp[2]
        self.idx_dict = temp[3]

    def tfidfVectorize(self, docs):
        '''
        Return tf-idf scores of docs

        Parameters:
            docs: list of strings, where each string is a complete document
        Returns:
            tuple of (TF-IDF matrix, list of feature names, idf array, and dictionary of feature indexes)
        '''
        tf = TfidfVectorizer(max_df=0.95)
        tfidf_matrix = tf.fit_transform(docs)
        feature_names = tf.get_feature_names()
        feature_idx_dict = {}
        for idx, elem in enumerate(feature_names):
            feature_idx_dict[elem] = idx
        return tfidf_matrix, feature_names, tf.idf_, feature_idx_dict

    def getRankings(self, query, county='', upper_limit=100):
        '''
        Compute resulting ranking cosine similarity between the query and corpus of docs represented
        by the TF-IDF matrix.

        parameters:
            query: string representing user's query
            clean_data[0]: List of doc_ids, ordered congruently to the corresponding
            rows of tfidf_matrix
            self.tfidf: TF-IDF matrix where each row corresponds to a document
            self.feat: List of all tokens, indexed corresponding to the columns
            of tfidf_matrix
            self.idf: List of all idf values, indexed per corresponding query index
            self.idx_dict: Dictionary of key: query, value: corresponding index
            in idf_array and feature_names
            upper_limit: maximum relevant results to be returned
            county: Optional input for case category
        returns:
            Sorted (ranked) list of doc_id, most relevant first
        '''
        if county!='':
            # DO SOMETHING
            pass
        query_tok_tfidf = {}
        query_split = query.split()
        query_idxs = []
        ret = []
        # Counting the frequency for valid query tokens
        for tok in query_split:
            if not tok in self.idx_dict:
                continue
            elif tok in query_tok_tfidf:
                query_tok_tfidf[tok] += 1
            else:
                query_tok_tfidf[tok] = 1
        # Multiplying term frequencies by idf
        for tok in query_tok_tfidf:
            idx = self.idx_dict[tok]
            idf_val = self.idf[idx]
            query_idxs.append(idx)
            query_tok_tfidf[tok] *= idf_val
        query_idxs.sort()
        query_tfidf_vec = np.zeros(len(self.idf))
        for i in range(len(query_idxs)):
            feature = self.feat[query_idxs[i]]
            query_tfidf_vec[query_idxs[i]] = query_tok_tfidf[feature]
        mag = np.sqrt(np.sum(query_tfidf_vec ** 2))
        query_tfidf_vec = np.divide(query_tfidf_vec, mag, out=np.zeros(len(self.idf),
            dtype=query_tfidf_vec.dtype), where=mag!=0)
        query_tfidf_csr_vec = sparse.csr_matrix(query_tfidf_vec)
        ranked_res = linear_kernel(query_tfidf_csr_vec, self.tfidf).flatten()
        sorted_idx_ranked_res = np.flip(np.argsort(ranked_res))[0:upper_limit:1]
        for i, idx in enumerate(sorted_idx_ranked_res):
            ret.append(self.clean_data[0][idx])
        return ret
