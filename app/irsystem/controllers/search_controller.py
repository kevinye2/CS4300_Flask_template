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
		resp_obj = legalTipResp(query)
		return Response(response=json.dumps(resp_obj), status=200,
			content_type='application/json')

@irsystem.route('/postfeedback', methods=['POST'])
def handleFeedback():
	with mutex:
		query = request.json.get('query')
		relevant_doc_id = request.json.get('relevant_rating')
		resp_obj = feedbackRatings(query, relevant_doc_id)
		return Response(response=json.dumps(resp_obj), status=200,
			content_type='application/json')
