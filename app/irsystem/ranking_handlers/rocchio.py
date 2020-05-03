from scipy import sparse
import numpy as np
from app.irsystem.ranking_handlers.tfidffunc import TFIDFHolder

class Rocchio():
    def __init__(self, tfidf_data):
        self.tfidf_obj = tfidf_data
        self.doc_idx_dict = tfidf_data.doc_idx_dict
        self.tfidf = tfidf_data.tfidf
        self.cur_query = None
        self.new_query = None
        self.cur_relevant_docs = None
        self.cur_irrelevant_docs = None

    def resetAll(self):
        self.cur_query = None
        self.new_query = None
        self.cur_relevant_docs = None
        self.cur_irrelevant_docs = None

    def addMultipleTraining(self, query, relevance_data):
        self.cur_query = self.tfidf_obj.vectorizeQuery(query)
        for doc_id in relevance_data:
            if not doc_id in self.doc_idx_dict:
                self.resetAll()
                return
            label = 1 if relevance_data[doc_id]['is_relevant'] else -1
            self.addTraining(doc_id, label)

    def addTraining(self, doc_id, label):
        doc_idx = self.doc_idx_dict[doc_id]
        data = self.tfidf[doc_idx:doc_idx + 1]
        if label == 1:
            if self.cur_relevant_docs is None:
                self.cur_relevant_docs = data
            else:
                self.cur_relevant_docs = sparse.vstack((self.cur_relevant_docs, data), format='csr')
        elif label == -1:
            if self.cur_irrelevant_docs is None:
                self.cur_irrelevant_docs = data
            else:
                self.cur_irrelevant_docs = sparse.vstack((self.cur_irrelevant_docs, data), format='csr')

    def produceNewQuery(self, a=0.9, b=0.9, c=0.6):
        if self.cur_query is None:
            return None
        asum = a * self.cur_query
        bsum = b * self.cur_relevant_docs.sum(axis=0) / self.cur_relevant_docs.shape[0] \
            if not self.cur_relevant_docs is None else None
        csum = c * self.cur_irrelevant_docs.sum(axis=0) / self.cur_irrelevant_docs.shape[0] \
            if not self.cur_irrelevant_docs is None else None
        self.new_query = asum
        if not bsum is None:
            self.new_query = self.new_query + bsum
        if not csum is None:
            self.new_query = self.new_query - csum
        self.new_query[self.new_query < 0] = 0
        return self.new_query
