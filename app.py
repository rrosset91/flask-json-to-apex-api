from flask import Flask, jsonify, make_response, request
from main import json2apex
import os

app = Flask(__name__)


@app.route("/json2apex", methods=["POST"])
def processjson():
    body = request.get_json()
    jsonContent = body["jsonContent"]
    className = request.args.get('className')
    generateTest = request.args.get('generateTest')
    auraEnabled = request.args.get('auraEnabled')
    parseMethod = request.args.get('parseMethod')
    convertedContent = json2apex(className, generateTest, jsonContent, auraEnabled, parseMethod)
    return convertedContent
    request.close()


@app.errorhandler(404)
def resource_not_found(e):
    return make_response(jsonify(error='Not found!'), 404)
