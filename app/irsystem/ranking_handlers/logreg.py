import random
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
from sklearn.linear_model import LogisticRegression

class LogReg():
    def __init__(self, tfidf_data, data_path, label_path):
        self.tfidf_obj = tfidf_data
        self.clean_data = tfidf_data.clean_data
        self.doc_idx_dict = tfidf_data.doc_idx_dict
        self.tfidf = tfidf_data.tfidf
        self.feat = tfidf_data.feat
        self.idf = tfidf_data.idf
        self.term_idx_dict = tfidf_data.term_idx_dict
        self.DATA_PATH = data_path
        self.LABEL_PATH = label_path
        try:
            self.accum_training = sparse.load_npz(self.DATA_PATH)
            self.accum_label = sparse.load_npz(self.LABEL_PATH)
        except Exception:
            self.accum_training = None
            self.accum_label = None

    def addTraining(self, query, doc_id, label):
        q = self.tfidf_obj.vectorizeQuery(query)
        doc_idx = self.doc_idx_dict[doc_id]
        data = self.tfidf[doc_idx:doc_idx + 1]
        concat = sparse.hstack((q, data), format='csr')
        label = label * np.ones((1))
        if self.accum_label is None or self.accum_training is None:
            self.accum_training = concat
            self.accum_label = sparse.csr_matrix(label)
        else:
            self.accum_training = sparse.vstack((self.accum_training, concat), format='csr')
            self.accum_label = sparse.hstack((self.accum_label, label), format='csr')

    def retrain(self):
        pass
