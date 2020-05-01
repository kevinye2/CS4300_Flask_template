from . import *
from app.irsystem.models.helpers import *
import random
import os
from scipy import sparse
import numpy as np
from app.irsystem.ranking_handlers.tfidffunc import TFIDFHolder

class Rocchio():
    def __init__(self, tfidf_data):
        self.tfidf_obj = tfidf_data
        self.doc_idx_dict = tfidf_data.doc_idx_dict
        self.tfidf = tfidf_data.tfidf
        self.cur_query = None
        self.cur_query_str = None
        self.new_query = None
        self.cur_relevant_docs = None
        self.cur_irrelevant_docs = None
        self.total_training = 0

    def resetAll(self):
        self.cur_query = None
        self.cur_query_str = None
        self.new_query = None
        self.cur_relevant_docs = None
        self.cur_irrelevant_docs = None
        self.total_training = 0

    def addTraining(self, query, doc_id, label, interval=5):
        if self.cur_query_str != query:
            self.resetAll()
            self.cur_query_str = query
            self.cur_query = self.tfidf_obj.vectorizeQuery(query)
        doc_idx = self.doc_idx_dict[doc_id]
        data = self.tfidf[doc_idx:doc_idx + 1]
        if label == 1:
            if self.cur_relevant_docs is None:
                self.cur_relevant_docs = data
            else:
                self.cur_relevant_docs = sparse.vstack((self.cur_relevant_docs, data), format='csr')
            self.total_training += 1
        elif label == -1:
            if self.cur_irrelevant_docs is None:
                self.cur_irrelevant_docs = data
            else:
                self.cur_irrelevant_docs = sparse.vstack((self.cur_irrelevant_docs, data), format='csr')
            self.total_training += 1
        if self.total_training > 0 and self.total_training % interval == 0:
            return self.produceNewQuery()
        return 200

    def produceNewQuery(self, a=0.9, b=0.9, c=0.3):
        self.new_query = (a * self.cur_query) + \
            (b * self.cur_relevant_docs.sum(axis=0) / self.cur_relevant_docs.shape[0]) - \
            (c * self.cur_irrelevant_docs.sum(axis=0) / self.cur_irrelevant_docs.shape[0])
        self.new_query[self.new_query < 0] = 0
        return 201
