# Import flask deps
from flask import request, render_template, \
	flash, g, session, redirect, url_for, jsonify, Response, abort

import json

# For decorators around routes
from functools import wraps

# Import socketio for socket creation in this module
from app import socketio

# Import module models
# from app.irsystem import search

# IMPORT THE BLUEPRINT APP OBJECT
from app.irsystem import irsystem
