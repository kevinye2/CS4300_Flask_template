# Methods to compose HTTP response JSON
from flask import jsonify
from flask import Response
import base64
import json
import numpy as np
import re
from bs4 import BeautifulSoup

def cleanText(s):
    '''
    Standard text cleaning and preprocessing:
    - lowercases
    - takes out punctuation and apostrophes
    - removes words that have 2 characters or fewer

    Parameters:
        s: string that represents the text to be processed
    Returns:
        processed string s
    '''
    s = s.lower()
    s = re.sub(r'[^ 0-9a-z]', ' ', s)
    s = ' '.join([word for word in s.split() if len(word) > 2])
    return s

def removeHTML(s):
    '''
    Remove all HTML tags and related elements from s; return cleaned string
    '''
    html_str = BeautifulSoup(s, features='html.parser')
    return html_str.get_text()

def http_json(result, bool):
	result.update({ "success": bool })
	return jsonify(result)


def http_resource(result, name, bool=True):
	resp = { "data": { name : result }}
	return http_json(resp, bool)


def http_errors(result):
	errors = { "data" : { "errors" : result.errors["_schema"] }}
	return http_json(errors, False)

class NumpyEncoder(json.JSONEncoder):

    def default(self, obj):
        """If input object is an ndarray it will be converted into a dict
        holding dtype, shape and the data, base64 encoded.
        """
        if isinstance(obj, np.ndarray):
            if obj.flags['C_CONTIGUOUS']:
                obj_data = obj.data
            else:
                cont_obj = np.ascontiguousarray(obj)
                assert(cont_obj.flags['C_CONTIGUOUS'])
                obj_data = cont_obj.data
            data_b64 = base64.b64encode(obj_data)
            return dict(__ndarray__=data_b64,
                        dtype=str(obj.dtype),
                        shape=obj.shape)
        # Let the base class default method raise the TypeError
        return json.JSONEncoder(self, obj)

def json_numpy_obj_hook(dct):
    """Decodes a previously encoded numpy ndarray with proper shape and dtype.
    :param dct: (dict) json encoded ndarray
    :return: (ndarray) if input was an encoded ndarray
    """
    if isinstance(dct, dict) and '__ndarray__' in dct:
        data = base64.b64decode(dct['__ndarray__'])
        return np.frombuffer(data, dct['dtype']).reshape(dct['shape'])
    return dct
