#from threading import Lock
from gevent.lock import RLock
from . import *
from app.irsystem.models.helpers import *
from app.irsystem.models.helpers import NumpyEncoder as NumpyEncoder
from app.irsystem.models.search import *

mutex = RLock()
@irsystem.route('/', methods=['GET'])
def initializeTemplate():
	with mutex:
		return render_template('search.html')

@irsystem.route('/postquery', methods=['POST'])
def handleQuery():
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
		resp_obj = legalTipResp(query, max_res, reddit_range_utc, ml_mode)
		return Response(response=json.dumps(resp_obj), status=200,
			content_type='application/json')

@irsystem.route('/postfeedback', methods=['POST'])
def handleFeedback():
	with mutex:
		query = request.json.get('query')
		relevant_doc_id = request.json.get('relevant_rating')
		ml_mode = int(request.json.get('ml_mode')) if not request.json.get('ml_mode') is None else 0
		resp_code = feedbackRatings(query, relevant_doc_id, ml_mode)
		return Response(response=json.dumps({}), status=resp_code,
			content_type='application/json')
