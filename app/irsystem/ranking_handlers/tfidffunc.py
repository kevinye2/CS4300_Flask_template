from app.irsystem.models.helpers import *
import random
import os
import time
import numpy as np
from scipy import sparse
from sklearn.metrics.pairwise import linear_kernel
from sklearn.feature_extraction.text import TfidfVectorizer

class TFIDFHolder():
    def __init__(self, clean_data):
        self.clean_data = clean_data
        self.doc_idx_dict = {}
        for i, doc_id in enumerate(self.clean_data[0]):
            self.doc_idx_dict[doc_id] = i
        temp = self.tfidfVectorize(self.clean_data[1])
        self.tfidf = temp[0]
        self.feat = temp[1]
        self.idf = temp[2]
        self.term_idx_dict = temp[3]
        self.stop_words = temp[4]

    def vectorizeQuery(self, query):
        '''
        Returns csr vectorized form of a query in respect to the tfidf
        '''
        query_tok_tfidf = {}
        query_split = query.split()
        query_idxs = []
        # Counting the frequency for valid query tokens
        for tok in query_split:
            if not tok in self.term_idx_dict:
                continue
            elif tok in query_tok_tfidf:
                query_tok_tfidf[tok] += 1
            else:
                query_tok_tfidf[tok] = 1
        # Multiplying term frequencies by idf
        for tok in query_tok_tfidf:
            idx = self.term_idx_dict[tok]
            idf_val = self.idf[idx]
            query_idxs.append(idx)
            query_tok_tfidf[tok] *= idf_val
        query_idxs.sort()
        query_tfidf_vec = np.zeros(len(query_idxs))
        query_tfidf_vec_pos = np.zeros(len(query_idxs))
        for i in range(len(query_idxs)):
            feature = self.feat[query_idxs[i]]
            query_tfidf_vec[i] = query_tok_tfidf[feature]
            query_tfidf_vec_pos[i] = query_idxs[i]
        mag = np.sqrt(np.sum(query_tfidf_vec ** 2))
        query_tfidf_vec = np.divide(query_tfidf_vec, mag, out=np.zeros(len(query_idxs),
            dtype=query_tfidf_vec.dtype), where=mag!=0)
        return sparse.csr_matrix((query_tfidf_vec, (np.zeros(len(query_idxs)), query_tfidf_vec_pos)),
            shape=(1, len(self.term_idx_dict)))

    def tfidfVectorize(self, docs):
        '''
        Return tf-idf scores of docs

        Parameters:
            docs: list of strings, where each string is a complete document
        Returns:
            tuple of (TF-IDF matrix, list of feature names, idf array, dictionary of feature indexes, and dictionary of stop words)
        '''
        tf = TfidfVectorizer(max_df=0.50)
        tfidf_matrix = tf.fit_transform(docs)
        feature_names = tf.get_feature_names()
        feature_idx_dict = {}
        for idx, elem in enumerate(feature_names):
            feature_idx_dict[elem] = idx
        return tfidf_matrix, feature_names, tf.idf_, feature_idx_dict, self.turnToDict(tf.stop_words_)

    def turnToDict(self, stop_words):
        ret = {}
        for word in stop_words:
            ret[word] = True
        return ret

    def getRankings(self, query, upper_limit=100):
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
            self.term_idx_dict: Dictionary of key: query, value: corresponding index
            in idf_array and feature_names
            upper_limit: maximum relevant results to be returned
        returns:
            Sorted (ranked) list of doc_id, most relevant first
        '''
        query_tok_tfidf = {}
        query_split = query.split()
        query_idxs = []
        ret = []
        # Counting the frequency for valid query tokens
        for tok in query_split:
            if not tok in self.term_idx_dict:
                continue
            elif tok in query_tok_tfidf:
                query_tok_tfidf[tok] += 1
            else:
                query_tok_tfidf[tok] = 1
        # Multiplying term frequencies by idf
        for tok in query_tok_tfidf:
            idx = self.term_idx_dict[tok]
            idf_val = self.idf[idx]
            query_idxs.append(idx)
            query_tok_tfidf[tok] *= idf_val
        query_idxs.sort()
        query_tfidf_vec = np.zeros(len(query_idxs))
        query_tfidf_vec_pos = np.zeros(len(query_idxs))
        for i in range(len(query_idxs)):
            feature = self.feat[query_idxs[i]]
            query_tfidf_vec[i] = query_tok_tfidf[feature]
            query_tfidf_vec_pos[i] = query_idxs[i]
        mag = np.sqrt(np.sum(query_tfidf_vec ** 2))
        query_tfidf_vec = np.divide(query_tfidf_vec, mag, out=np.zeros(len(query_idxs),
            dtype=query_tfidf_vec.dtype), where=mag!=0)
        query_tfidf_csr_vec = sparse.csr_matrix((query_tfidf_vec, (np.zeros(len(query_idxs)), query_tfidf_vec_pos)),
            shape=(1, len(self.term_idx_dict)))
        ranked_res = linear_kernel(query_tfidf_csr_vec, self.tfidf).flatten()
        sorted_idx_ranked_res = np.flip(np.argsort(ranked_res))
        sorted_idx_ranked_res = sorted_idx_ranked_res[0:min(upper_limit, sorted_idx_ranked_res.size):1]
        for i, idx in enumerate(sorted_idx_ranked_res):
            ret.append(self.clean_data[0][idx])
        return ret

    def getRankingsWithQueryVector(self, query_vector, upper_limit=100):
        '''
        Compute resulting ranking cosine similarity between the query and corpus of docs represented
        by the TF-IDF matrix.

        parameters:
            query_vector: query vector, csr form
            clean_data[0]: List of doc_ids, ordered congruently to the corresponding
            rows of tfidf_matrix
            self.tfidf: TF-IDF matrix where each row corresponds to a document
            self.feat: List of all tokens, indexed corresponding to the columns
            of tfidf_matrix
            self.idf: List of all idf values, indexed per corresponding query index
            self.term_idx_dict: Dictionary of key: query, value: corresponding index
            in idf_array and feature_names
            upper_limit: maximum relevant results to be returned
        returns:
            Sorted (ranked) list of doc_id, most relevant first
        '''
        ret = []
        ranked_res = linear_kernel(query_vector, self.tfidf).flatten()
        sorted_idx_ranked_res = np.flip(np.argsort(ranked_res))
        sorted_idx_ranked_res = sorted_idx_ranked_res[0:min(upper_limit, sorted_idx_ranked_res.size):1]
        for i, idx in enumerate(sorted_idx_ranked_res):
            ret.append(self.clean_data[0][idx])
        return ret
