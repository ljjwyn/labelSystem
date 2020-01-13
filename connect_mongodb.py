#!/usr/bin/python3
import re
import json
import pymongo
from itertools import groupby
from operator import itemgetter
import pandas as pd
from testNEO import insertInitRecord, updateEntityLabel, insertRecord


def check_contain_chinese(check_str):
    for ch in check_str:
        if u'\u4e00' <= ch <= u'\u9fff':
            return True
    return False


"""
将爬取的目录属性信息加载到neo4j数据库中，这里涉及到一个
实体的类别的问题，在使用本函数加载的过程中先设置为默认模型
"""


def recordNEO4J():
    myclient = pymongo.MongoClient('mongodb://localhost:27017/')
    mydb = myclient['BaiKe4']
    mycol = mydb["keyWordsContent"]
    neo4jList = list()
    count = 0
    for i in mycol.find({}):
        if len(i)==7:
            relationList = i['catalog']
            contentList = i['content']
            title = i['title']
            if len(relationList)==len(contentList):
                if 'ISBN：' not in relationList:
                    for i in range(len(relationList)):
                        if contentList[i] != title:
                            tempMap4 = {
                                "entity1": title.split("[")[0],
                                "entity2": contentList[i].split("[")[0],
                                "relation": relationList[i][:-1]
                            }
                            neo4jList.append(tempMap4)
                    count += 1
        if count > 1000:
            break
    # 记录neo4j数据库函数
    insertInitRecord(neo4jList)


def search_keywords(content):
    myclient = pymongo.MongoClient('mongodb://localhost:27017/')
    mydb = myclient['BaiKe4']
    mycol = mydb["keyWordsContent"]
    res = []
    print(content)
    for i in mycol.find({"summary": re.compile(content)}):
        tempMap= {'ID': i['ID'], 'title': i['title'], 'imgUrl':'', 'summarys': ''}
        tempMap['imgUrl']=i['imgUrl'][0:-5]+"140.jpg"
        for s in i['summary']:
            tempMap['summarys']+=s
        tempMap['summarys']=tempMap['summarys'][0:100]
        tempMap['summarys']+="..."
        res.append(tempMap)
        if len(res) >= 50:
            break
    for i in mycol.find({"content": re.compile(content)}):
        tempMap= {'ID': i['ID'], 'title': i['title'], 'imgUrl':'', 'summarys': ''}
        tempMap['imgUrl']=i['imgUrl'][0:-5]+"140.jpg"
        for s in i['summary']:
            tempMap['summarys']+=s
        tempMap['summarys']=tempMap['summarys'][0:100]
        tempMap['summarys']+="..."
        res.append(tempMap)
        # if len(res)>=20:
        #     break
    if len(res) > 90:
        res = res[0:50]
    res = json.dumps(res, ensure_ascii=False)
    print(res)
    myclient.close()
    return res


def search_item(ID):
    myclient = pymongo.MongoClient('mongodb://localhost:27017/')
    mydb = myclient['BaiKe4']
    mycol = mydb["keyWordsContent"]
    res=''
    for i in mycol.find({"ID": int(ID)}):
        temp=''
        del (i['_id'])
        for s in i['summary']:
            temp+=s
        i['summary']=temp
        print(i)
        res = i
    res = json.dumps(res, ensure_ascii=False)
    print(res)
    myclient.close()
    return res


def get_item():
    record_ID = get_current_ID()
    currentID = record_ID
    myclient = pymongo.MongoClient('mongodb://localhost:27017/')
    mydb = myclient['BaiKe4']
    mycol = mydb["keyWordsContent"]
    while not [x for x in mycol.find({"ID": currentID})]:
        currentID+=1
    res=''
    for i in mycol.find({"ID": currentID}):
        del (i['_id'])
        temp = ''
        for s in i['summary']:
            temp += s
        i['summary'] = temp
        res = i
    currentID += 1
    record_num(record_ID, currentID, res['title'])
    res = json.dumps(res, ensure_ascii=False)
    print(res)
    myclient.close()
    return res


def record_num(oldnum, num, title):
    myclient = pymongo.MongoClient('mongodb://localhost:27017/')
    mydb = myclient['BaiKe4']
    mycol = mydb["recordNum"]
    #mycol.insert({"ID":1,"title":"深度学习","oldId":0})
    mycol.update({"ID": oldnum}, {'$set': {"ID": num, "title": title, "oldId": oldnum}})
    myclient.close()


def get_current_ID():
    myclient = pymongo.MongoClient('mongodb://localhost:27017/')
    mydb = myclient['BaiKe4']
    mycol = mydb["recordNum"]
    col = mycol.find()
    for C in col:
        ID = C['ID']
    myclient.close()
    return ID


def relation_label(keys):
    myclient = pymongo.MongoClient('mongodb://localhost:27017/')
    mydb = myclient['BaiKe4']
    mycol = mydb["keyWordsContent"]
    sentence=[]
    count=0
    summary=[]
    for i in mycol.find():
        summary.extend(i['summary'])
    myclient.close()
    for S in summary:
        S.split('。')
        sentence.append(S)
    for S in sentence:
        entityList=[]
        for K in keys:
            if K in S:
                print(K)
                entityList.append(K)
        if entityList:
            print(entityList)
            recordEntity(S,entityList,count)
            print("__________处理个数_"+str(count)+"_____________")
            count += 1


def recordEntity(sentence,entity,count):
    myclient = pymongo.MongoClient('mongodb://localhost:27017/')
    mydb = myclient['BaiKe4']
    mycol = mydb["sentenceEntity"]
    mycol.insert({"ID":count,"sentence":sentence,"entity":entity})
    myclient.close()


def get_keywords():
    myclient = pymongo.MongoClient('mongodb://localhost:27017/')
    mydb = myclient['BaiKe4']
    mycol = mydb["keyWordsContent"]
    keyWordsList = []
    for i in mycol.find():
        keys = i['title'].split("[")[0]
        if len(keys)>1:
            keyWordsList.append(keys)
    myclient.close()
    return keyWordsList


def recordLabel(entity,label,ID):
    entity = entity.split("[")[0]
    myclient = pymongo.MongoClient('mongodb://localhost:27017/')
    mydb = myclient['BaiKe4']
    mycol = mydb["labeledEntity"]
    mycol.insert({"ID": ID, "entity": entity, "label": label})
    myclient.close()
    f = open('label', 'a+')
    f.write(entity+" "+label+"\n")
    f.close()
    res = {
        "state":"success"
    }
    res = json.dumps(res)
    return res


def getUpdateCount(flag, dataBaseName):
    myclient = pymongo.MongoClient('mongodb://localhost:27017/')
    mydb = myclient[dataBaseName]
    mycol = mydb[flag]
    print(flag)
    col = mycol.find()
    count = 0
    for C in col:
        count = C['count']
    print(count)
    mycol.update({"count": count}, {'$set': {"count": count+1}})
    myclient.close()
    return count


def getCount(flag, dataBaseName):
    myclient = pymongo.MongoClient('mongodb://localhost:27017/')
    mydb = myclient[dataBaseName]
    mycol = mydb[flag]
    col = mycol.find()
    for C in col:
        count = C['count']
    myclient.close()
    return count


def recordLabelEntity(entity, entityType, sentence, userId, dataSetId):
    dataBaseName = 'labelEntityRelation' + str(userId)
    countDataSetName = "countEntity" + str(dataSetId)
    ID = getUpdateCount(countDataSetName, dataBaseName)
    ID += 1
    myclient = pymongo.MongoClient('mongodb://localhost:27017/')
    mydb = myclient[dataBaseName]
    colName = "labelEntity" + str(dataSetId)
    mycol = mydb[colName]
    mycol.insert({"ID": ID, "entity":entity,"entityType":entityType, "sentence": sentence})
    myclient.close()
    entityMap = {
        "entity": entity,
        "entity_type": entityType
    }
    updateEntityLabel(entityMap)
    return ID


def recordLabelRelation(entity1, entity2, relation, sentence, userId, dataSetId):
    dataBaseName = 'labelEntityRelation' + str(userId)
    countDataSetName = "countRelation" + str(dataSetId)
    ID = getUpdateCount(countDataSetName, dataBaseName)
    ID += 1
    myclient = pymongo.MongoClient('mongodb://localhost:27017/')
    mydb = myclient[dataBaseName]
    colName = "labelRelation" + str(dataSetId)
    mycol = mydb[colName]
    mycol.insert({"ID": ID, "entity1": entity1, "relation": relation, "entity2": entity2, "sentence": sentence})
    relationMap = {
        "entity1": entity1,
        "entity2": entity2,
        "relation": relation
    }
    insertRecord(relationMap)
    myclient.close()
    return ID


def createSentence(dataSetName, dataSetColName, userId, dataSetId):
    dataBaseName = 'labelEntityRelation' + str(userId)
    myclient = pymongo.MongoClient('mongodb://localhost:27017/')
    mydb = myclient[dataBaseName]
    colName = "contents"+ str(dataSetId)
    mycol = mydb[colName]
    countColName = 'countContents' + str(dataSetId)
    mycolCount = mydb[countColName]
    countRelName = 'countRelation' + str(dataSetId)
    mycolCount1 = mydb[countRelName]
    mycol.drop()
    mycolCount.drop()
    mycolCount1.drop()
    myclient.close()
    myclient = pymongo.MongoClient('mongodb://localhost:27017/')
    mydb = myclient[dataSetName]
    mycol = mydb[dataSetColName]
    col = mycol.find()
    sentenceList = list()
    for C in col:
        sentence = C['sentence']
        sentenceList.extend(sentence.split("。"))
    myclient.close()
    myclient = pymongo.MongoClient('mongodb://localhost:27017/')
    mydb = myclient[dataBaseName]
    mycol = mydb[colName]
    count = 1
    for sentence in sentenceList:
        if sentence != '':
            mycol.insert({"ID": count, "sentence": sentence, "flag":0})
            count += 1
    myclient.close()
    myclient = pymongo.MongoClient('mongodb://localhost:27017/')
    mydb = myclient[dataBaseName]
    countColName='countContents'+str(dataSetId)
    mycol = mydb[countColName]
    mycol.insert({"count": 0})
    myclient.close()
    myclient = pymongo.MongoClient('mongodb://localhost:27017/')
    mydb = myclient[dataBaseName]
    countColName = 'countRelation' + str(dataSetId)
    mycol = mydb[countColName]
    mycol.insert({"count": 0})
    myclient.close()
    print("重建数据集完成")
    return "success"


def loadSentence(userId, dataSetId):
    countDataSetName = "countContents"+str(dataSetId)
    dataBaseName = 'labelEntityRelation' + str(userId)
    ID = getUpdateCount(countDataSetName, dataBaseName)
    ID += 1
    myclient = pymongo.MongoClient('mongodb://localhost:27017/')
    mydb = myclient[dataBaseName]
    colName = "contents"+str(dataSetId)
    mycol = mydb[colName]
    for i in mycol.find({"ID": ID}):
        sentence = i['sentence']
        ID = i['ID']
        mycol.update({"ID": ID}, {'$set': {"flag": 1}})
    myclient.close()
    print(sentence)
    res = {
        "sentence": sentence,
        "ID": ID
    }
    print(res)
    res = json.dumps(res, ensure_ascii=False)
    return res


def searchContext(content, userId, dataSetId):
    dataBaseName = 'labelEntityRelation' + str(userId)
    myclient = pymongo.MongoClient('mongodb://localhost:27017/')
    mydb = myclient[dataBaseName]
    colName = "contents" + str(dataSetId)
    mycol = mydb[colName]
    count = 0
    for j in mycol.find({"sentence": re.compile(content)}):
        count += 1
    currentNum = 0
    sentence = ''
    ID = None
    for i in mycol.find({"sentence": re.compile(content)}):
        currentNum += 1
        flag = i['flag']
        if flag == 0:
            sentence = i['sentence']
            ID = i['ID']
            mycol.update({"ID": ID}, {'$set': {"flag": 1}})
            break
        print(sentence)
    resMap = {
        "sumCount": count,
        "currentNum": currentNum,
        "sentence": sentence,
        "ID": ID
    }
    res = json.dumps(resMap, ensure_ascii=False)
    myclient.close()
    return res


def loadLabeledDataSet(userId, dataSetId):
    dataBaseName = 'labelEntityRelation' + str(userId)
    myclient = pymongo.MongoClient('mongodb://localhost:27017/')
    mydb = myclient[dataBaseName]
    colName = "labelEntity" + dataSetId
    mycol = mydb[colName]
    entityList = list()
    categoriesList = list()
    for i in mycol.find():
        tempMap = {
            "entity": i["entity"],
            "entity_type": i["entityType"],
            "sentence": i["sentence"]
        }
        entityList.append(tempMap)
        categoriesList.append(i["entityType"])
    myclient.close()
    myclient = pymongo.MongoClient('mongodb://localhost:27017/')
    mydb = myclient[dataBaseName]
    colName = "labelRelation" + dataSetId
    mycol = mydb[colName]
    relationList = list()
    for i in mycol.find():
        tempMap = {
            "entity1": i["entity1"],
            "entity2": i["entity2"],
            "relation": i["relation"],
            "sentence": i["sentence"]
        }
        relationList.append(tempMap)
    myclient.close()
    entityList = distinct(entityList, "entity")
    categories = list(set(categoriesList))
    resultMap = {
        "entityList": entityList,
        "relationList": relationList,
        "categories": categories
    }
    print(resultMap)
    resultMap = json.dumps(resultMap, ensure_ascii=False)
    return resultMap


def distinct(items, key):
    key = itemgetter(key)
    items = sorted(items, key=key)
    return [next(v) for _, v in groupby(items, key=key)]


def createDataSet(userId, dataSetId):
    dataBaseName = 'labelEntityRelation' + str(userId)
    myclient = pymongo.MongoClient('mongodb://localhost:27017/')
    mydb = myclient[dataBaseName]
    colName = "labelRelation" + str(dataSetId)
    mycol = mydb[colName]
    contents = 'sentence,relation,head,head_type,head_offset,tail,tail_type,tail_offset\n'
    resContents = ''
    count = 0
    relationList = list()
    for i in mycol.find():
        sentence = i["sentence"]
        head_offset = sentence.index(i["entity1"])
        tail_offset = sentence.index(i["entity2"])
        relation = i["relation"]
        relationList.append(relation)
        if head_offset > tail_offset:
            entity1 = i["entity1"]
            entity2 = i["entity2"]
        else:
            entity1 = i["entity2"]
            entity2 = i["entity1"]
        myclient1 = pymongo.MongoClient('mongodb://localhost:27017/')
        mydb1 = myclient1[dataBaseName]
        colName = "labelEntity" + str(dataSetId)
        mycol1 = mydb1[colName]
        entity1_type = 'None'
        entity2_type = 'None'
        for j in mycol1.find({"entity": entity1}):
            entity1_type = j['entityType']
        for j in mycol1.find({"entity": entity2}):
            entity2_type = j['entityType']
        myclient1.close()
        contents += sentence + "," + relation + "," + entity1 + "," + entity1_type + "," + str(
            head_offset) + "," + entity2 + "," + entity2_type + "," + str(tail_offset) + "\n"
        if count < 10:
            resContents = contents
        count += 1
    print(contents)
    relationList = list(set(relationList))
    relationClass = ''
    for Class in relationList:
        relationClass += Class + '\n'
    filename = '/home/jiajie/test/data/download/RETrain'
    with open(filename, 'w') as file_object:
        file_object.write(contents)
    filename = '/home/jiajie/test/data/download/Class'
    with open(filename, 'w') as file_object:
        file_object.write(relationClass)
    myclient.close()
    resultMap = {
        "contents": resContents,
        "relation": relationClass
    }
    print(resultMap)
    resultMap = json.dumps(resultMap, ensure_ascii=False)
    return resultMap


def checkDataSet(userId, dataSetId):
    myclient = pymongo.MongoClient('mongodb://localhost:27017/')
    userDB = 'labelEntityRelation' + str(userId)
    mydb = myclient[userDB]
    userTable = "contents" + str(dataSetId)
    mycol = mydb[userTable]
    col = mycol.find({"ID": 1})
    flag = 0
    for i in col:
        if i["ID"]:
            flag = 1
    resultMap = {
        "isDataBase": flag
    }
    print(resultMap)
    resultMap = json.dumps(resultMap)
    return resultMap


if __name__=="__main__":
    pass
    # recordNEO4J()
    # pass
    # createSentence("BaiKe4", "sentenceEntity", "1")
    #createSentence()
    # myclient = pymongo.MongoClient('mongodb://localhost:27017/')
    # mydb = myclient['BaiduXueshu2']
    # mycol = mydb["relatePaper"]
    # col = mycol.find()
    # sentenceList = list()
    # for C in col:
    #     sentence = C['abstract']
    #     if sentence:
    #         sentenceList.extend(sentence.split("。"))
    # myclient.close()
    # myclient = pymongo.MongoClient('mongodb://localhost:27017/')
    # mydb = myclient['BaiduXueshu']
    # mycol = mydb["abstract"]
    # count = 1
    # for sentence in sentenceList:
    #     if sentence != '':
    #         mycol.insert({"ID": count, "sentence": sentence})
    #         count += 1
    # myclient.close()
