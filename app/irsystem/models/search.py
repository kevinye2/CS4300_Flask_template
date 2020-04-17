from . import *
from app.irsystem.models.helpers import *
import random
import string
import requests

def getCases(query, county):
    '''
    parameters:
        query: string describing user legal help request for COVID-19
        county: string describing which county the user is in
    returns:
        list of tuples in the form of
            [
                ('Statute title', 'description', id, url),
                ...
            ],
    '''
    ###does not filter by county yet###
    r = requests.get('https://api.case.law/v1/cases/?search='+ query + '&jurisdiction=ny&full_case=true&body_format=html')
    data = r.json()
    all_cases = []
    for case in data['results']:
        all_cases.append((case['name'], case['preview'], case['id'], case['frontend_url']))
    return all_cases

def legalTipResp(query, county):
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
    ###Follow the template; replace this code###
    resp_object = {}
    temp = []
    total_string = string.ascii_lowercase + string.ascii_uppercase + string.digits
    for i in range(107):
        temp_title = ''
        temp_content = ''
        for j in range(100):
            for k in range(random.choice(range(1, 21))):
                if j < 20:
                    temp_title += random.choice(total_string)
                temp_content += random.choice(total_string)
            temp_title += ' '
            temp_content += ' '
        temp.append((
            str(i) + temp_title + str(i),
            str(i) + temp_content + str(i),
            'code_' + str(i*i),
            'https://legislation.nysenate.gov/static/docs/html/index.html#'))
    resp_object['legal_codes'] = temp
    # temp = []
    # for i in range(94):
    #     temp_title = ''
    #     temp_content = ''
    #     for j in range(100):
    #         for k in range(random.choice(range(1, 21))):
    #             if j < 20:
    #                 temp_title += random.choice(total_string)
    #             temp_content += random.choice(total_string)
    #         temp_title += ' '
    #         temp_content += ' '
    #     temp.append((
    #         str(i) + temp_title + str(i),
    #         str(i) + temp_content + str(i),
    #         'case_' + str(i*i),
    #         'https://case.law/'))
    # resp_object['legal_cases'] = temp
    ###getting Caselaw data from API using helper function getCases()###
    resp_object['legal_cases'] = getCases(query, county)
    temp = []
    for i in range(93):
        temp_title = ''
        temp_content = ''
        for j in range(100):
            for k in range(random.choice(range(1, 21))):
                if j < 20:
                    temp_title += random.choice(total_string)
                temp_content += random.choice(total_string)
            temp_title += ' '
            temp_content += ' '
        temp.append((
            str(i) + temp_title + str(i),
            str(i) + temp_content + str(i),
            'reddit_' + str(i*i),
            'https://reddit.com'))
    resp_object['reddit_posts'] = temp
    ###Follow the template; replace this code###
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
    return {'Great 1' : relevant_doc_id[0], 'Great 2' : relevant_doc_id[1]}
