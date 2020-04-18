from multiprocessing import Lock
from . import *
from app.irsystem.models.helpers import *
from app.irsystem.models.helpers import NumpyEncoder as NumpyEncoder
from app.irsystem.models.search import *

mutex = Lock()
@irsystem.route('/', methods=['GET'])
def initializeTemplate():
	with mutex:
		return render_template('search.html')

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
