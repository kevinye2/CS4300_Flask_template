#from threading import Lock
from gevent.lock import RLock
from . import *
from app.irsystem.models.helpers import *
from app.irsystem.models.helpers import NumpyEncoder as NumpyEncoder
from app.irsystem.models.search import *

mutex = RLock()
global_counter = 0
global_array = []
@irsystem.route('/', methods=['GET'])
def initializeTemplate():
	with mutex:
		return render_template('search.html')

@irsystem.route('/inccounter', methods=['GET'])
def incCounter():
	global global_counter
	global_counter += 1
	global_array.append(global_counter)
	return Response('INCR', status=200,
			content_type='text/plain')

@irsystem.route('/globalcounter', methods=['GET'])
def getCounter():
	return Response(response=json.dumps({'lst':global_array}), status=200,
		content_type='application/json')

@irsystem.route('/postquery', methods=['POST'])
def handleQuery():
	with mutex:
		query = request.json.get('query')
		county = request.json.get('county')
		resp_obj = legalTipResp(query, county)
		return Response(response=json.dumps(resp_obj), status=200,
			content_type='application/json')

@irsystem.route('/postfeedback', methods=['POST'])
def handleFeedback():
	with mutex:
		query = request.json.get('query')
		county = request.json.get('county')
		relevant_doc_id = request.json.get('relevant_rating')
		resp_obj = feedbackRatings(query, county, relevant_doc_id)
		return Response(response=json.dumps(resp_obj), status=200,
			content_type='application/json')
