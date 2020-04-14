from . import *
from app.irsystem.models.helpers import *

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
    for i in range(3):
        temp.append(('NYS Law ' + str(i), 'law ' + str(i), 'code_' + str(i*i), 'https://legislation.nysenate.gov/static/docs/html/index.html#'))
    resp_object['legal_codes'] = temp
    temp = []
    for i in range(3):
        temp.append(('Ithaca case ' + str(i), 'case ' + str(i), 'case_' + str(i*i), 'https://case.law/'))
    resp_object['legal_cases'] = temp
    temp = []
    for i in range(3):
        temp.append(('Reddit ' + str(i), 'r/Cornell ' + str(i), 'reddit_' + str(i*i), 'https://reddit.com'))
    resp_object['reddit_posts'] = temp
    ###Follow the template; replace this code###
    return resp_object

def feedbackRatings(query, county, relevant_doc_ids):
    '''
    parameters:
        query: original string query
        county: original county selection
        relevant_doc_ids: list of [doc_id, ranking] deeemed relevant to query and county;
        ranking is the original ranking provided by the system for the
        document in regards to its category (statutes, cases, reddit posts)
    '''
    ###Perform analysis on the relevancy rating###
    return {'Great' : True}
