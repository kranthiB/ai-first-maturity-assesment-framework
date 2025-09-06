"""Questions API blueprint"""
from flask import Blueprint

questions_api = Blueprint('questions_api', __name__)

@questions_api.route('/')
def index():
    return {'message': 'Questions API', 'status': 'ok'}
