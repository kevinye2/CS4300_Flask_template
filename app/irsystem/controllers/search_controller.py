#from threading import Lock
from gevent.lock import RLock
from . import *
from app.irsystem.models.helpers import *
from app.irsystem.models.search import *

mutex = RLock()
@irsystem.route('/', methods=['GET'])
def initializeTemplate():
	with mutex:
		return render_template('search.html')

@irsystem.route('/postquery', methods=['POST'])
def handleQuery():
	'''
	The EXPECTED incoming request is a json of the form:
	{
		max_res: integer representing the number of maximum results to be returned per category,
		ml_mode: integer identifier in the range [0, 1, 2], with 0 being no relevance feedback,
			1 representing logistic regression, and 2 representing Rocchio,
		query: Query string with alphanumeric characters only,
		reddit_range_utc: array of length 2 specifying the beginning and end UTC
			time in seconds of reddit posts that should be returned, ie. [1000000000, 2000000000],
		relevance_feedbacks: a json object (dictionary) of the form:
		{
			'codes_info':
			{
				'query':
				{
					'doc_id':
					{
						is_relevant: true or false,
						ranking: original ranking of document, integer
					},
					...
				},
				...
			},
			'cases_info':
			{
				[same format as 'codes_info']
			},
			'reddit_info':
			{
				[same format as 'codes_info']
			}
		}
	}
	'''
	with mutex:
		query = request.json.get('query')
		max_res = int(request.json.get('max_res')) if not request.json.get('max_res') is None else 50
		reddit_range_utc = request.json.get('reddit_range_utc')
		if not reddit_range_utc is None:
			reddit_range_utc[0] = int(reddit_range_utc[0])
			reddit_range_utc[1] = int(reddit_range_utc[1])
		else:
			reddit_range_utc = [0, 2 * (10**9)]
		ml_mode = int(request.json.get('ml_mode')) if not request.json.get('ml_mode') is None else 0
		relevance_feedbacks = request.json.get('relevance_feedbacks')
		resp_obj = legalTipResp(query, max_res, reddit_range_utc, ml_mode, relevance_feedbacks)
		return Response(response=json.dumps(resp_obj), status=200,
			content_type='application/json')
