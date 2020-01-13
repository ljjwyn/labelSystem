import json
from flask import Flask, Response, request
from connect_mongodb import *
from testNEO import searchDB, fuzzySearch

app = Flask(__name__)


#实现跨域访问
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,session_id')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS,HEAD')
    # 这里不能使用add方法，否则会出现 The 'Access-Control-Allow-Origin' header contains multiple values 的问题
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


@app.route("/check")
def getUser():
    result = {'username': 'lijiajie', 'password': 'wangyanan'}
    return Response(json.dumps(result), mimetype='application/json')


@app.route("/searchKeywords",methods=['POST'])
def searchitem():
    data=request.json
    res=search_keywords(data['keywords'])
    return res


@app.route("/getItem",methods=['POST'])
def getitem():
    data=request.json
    res=search_item(data['ID'])
    return res


@app.route("/noLabelItem",methods=['GET'])
def noLabelItem():
    res=get_item()
    return res


@app.route("/recordlabel",methods=['POST'])
def recordlabel():
    data = request.json
    res=recordLabel(data['entity'],str(data['label']),data['ID'])
    return res


@app.route("/recordentity",methods=['POST'])
def recordentity():
    data = request.json
    res=recordLabelEntity(str(data['entity']),str(data['entityType']), str(data['sentence'])
                          , str(data['userId']), str(data['dataSetId']))
    return str(res)


@app.route("/recordrelation",methods=['POST'])
def recordrelation():
    data = request.json
    res=recordLabelRelation(str(data['entity1']), str(data['entity2']), str(data['relation']),
                            str(data['sentence']), str(data['userId']), str(data['dataSetId']))
    return str(res)


@app.route("/getsentence",methods=['POST'])
def getsentence():
    data = request.json
    res = loadSentence(str(data['userId']), str(data['dataSetId']))
    return res


@app.route("/rebuilddataset",methods=['POST'])
def rebuilddataset():
    data = request.json
    res = createSentence(str(data['dataSetName']), str(data['dataSetColName']), str(data['userId']), str(data['dataSetId']))
    return res


@app.route("/searchcontext",methods=['POST'])
def searchcontext():
    data = request.json
    res=searchContext(str(data['content']), str(data['userId']), str(data['dataSetId']))
    return res


@app.route("/getlabeledinfo",methods=['POST'])
def getlabeledinfo():
    data = request.json
    res = loadLabeledDataSet(str(data['userId']), str(data['dataSetId']))
    return res


@app.route("/createdataset",methods=['POST'])
def createdataset():
    data = request.json
    res = createDataSet(str(data['userId']), str(data['dataSetId']))
    return res


@app.route("/checkdataset",methods=['POST'])
def checkdataset():
    data = request.json
    res = checkDataSet(str(data['userId']), str(data['dataSetId']))
    return res


@app.route("/searchentityinfo",methods=['POST'])
def searchentityinfo():
    data = request.json
    res = searchDB(str(data['searchContent']), int(data['deep']))
    return res


@app.route("/fuzzysearch",methods=['POST'])
def fuzzysearch():
    data = request.json
    res = fuzzySearch(str(data['searchContent']))
    return res


app.run(port=3001, host='0.0.0.0')
