"""Assessments API blueprint"""
from flask import Blueprint

assessments_api = Blueprint('assessments_api', __name__)

@assessments_api.route('/')
def index():
    return {'message': 'Assessments API', 'status': 'ok'}
