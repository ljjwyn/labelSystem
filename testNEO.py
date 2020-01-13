# coding:utf-8
# 自创的neo4j图数据库的广度优先遍历算法
# 可以指定检索深度
import json

from py2neo import Graph, Node, Relationship
from itertools import groupby
from operator import itemgetter
import pandas as pd


def insertInitRecord(neo4jList):
    graph = Graph('http://localhost:7474', username='neo4j', password='root')
    count = 0
    for tempMap in neo4jList:
        print("插入第"+str(count))
        count+=1
        a = Node("初始化实体类别", name=tempMap['entity1'])
        graph.create(a)
        b = Node("属性值", name=tempMap['entity2'])
        graph.create(b)
        r = Relationship(a, tempMap['relation'], b)
        graph.create(r)
        print(r)


def updateEntityLabel(entityMap):
    graph = Graph('http://localhost:7474', username='neo4j', password='root')
    res = graph.run("MATCH (n {name:\""+entityMap.get('entity')+"\"}) SET n.newLabel=\""
                    +entityMap.get('entity_type')+"\" RETURN n").data()
    if len(res) <= 0:
        a = Node(entityMap.get('entity_type'), name=entityMap.get('entity'))
        graph.create(a)
        print("插入新实体")
    else:
        print("修改完成")


def insertRecord(tempMap):
    graph = Graph('http://localhost:7474', username='neo4j', password='root')
    resultList = graph.run("match (n {name:\"" + tempMap.get('entity1') + "\"}) return n").data()
    entity = resultList[0].get('n').get('name')
    if resultList[0].get('n').get('newLabel'):
        entity_type = resultList[0].get('n').get('newLabel')
    else:
        entity_type = str(resultList[0].get('n')).split(':')[1].split(' {')[0]
    a = Node(entity_type, name=entity)
    resultList = graph.run("match (n {name:\"" + tempMap.get('entity2') + "\"}) return n").data()
    entity2 = resultList[0].get('n').get('name')
    if resultList[0].get('n').get('newLabel'):
        entity2_type = resultList[0].get('n').get('newLabel')
    else:
        entity2_type = str(resultList[0].get('n')).split(':')[1].split(' {')[0]
    b = Node(entity2_type, name=entity2)
    r = Relationship(a, tempMap['relation'], b)
    graph.create(r)
    print(r)


def clearDB():
    graph = Graph('http://localhost:7474', username='neo4j', password='root')
    # match (n) detach delete n
    graph.run("match (n) detach delete n")


def testInsert():
    graph = Graph('http://localhost:7474', username='neo4j', password='root')
    a = Node("人物", name="李佳洁")
    graph.create(a)
    b = Node("人物", name="王雅楠")
    graph.create(b)
    r = Relationship(a, "夫妻", b)
    graph.create(r)


def fuzzySearch(content):
    graph = Graph('http://localhost:7474', username='neo4j', password='root')
    resultList = graph.run("match (n)-[r]-(m) where  n.name Contains  '" + content + "' return n,m,r").data()
    entityList = list()
    if len(resultList) == 0:
        resultMap = {
            "state": 0,
        }
        print(resultMap)
        resultMap = json.dumps(resultMap, ensure_ascii=False)
        return resultMap
    else:
        for res in resultList:
            entityList.append(res.get('n').get('name'))
        contentList_temp = list(set(entityList))
        contentList_temp.sort(key=entityList.index)
        if len(contentList_temp) > 30:
            contentList_temp = contentList_temp[0:30]
        resultMap = {
            "state": 1,
            "entityList": contentList_temp
        }
        print(resultMap)
        resultMap = json.dumps(resultMap, ensure_ascii=False)
        return resultMap


'''
自创的基于广度优先的搜说遍历方法，设置需要检索的图谱深度，并通过
特别的循环结构生成关系方向正确的键值对。
'''


def searchDB(content, deep):
    from py2neo import NodeMatcher
    graph = Graph('http://localhost:7474', username='neo4j', password='root')
    matcher = NodeMatcher(graph)
    # a=matcher.match("人物", name="李佳洁").first()
    # print(a)
    contentList = list()
    contentList_temp = list()
    contentList.append(content)
    contentList_temp.append(content)
    relationList = list()
    entityList = list()
    categoriesList = list()
    countContent = 1
    deepCount = 0
    countList = list()
    countList.append(0)
    resultList = graph.run("match (n {name:\"" + content + "\"})-[r]-(m) return n,m,r").data()
    if len(resultList) == 0:
        resultMap = {
            "state": 0,
        }
        print(resultMap)
        resultMap = json.dumps(resultMap, ensure_ascii=False)
        return resultMap
    else:
        while deepCount < deep:
            countList.append(len(contentList_temp))
            for i in range(countList[deepCount], countList[deepCount + 1]):
                resultList = graph.run("match (n {name:\"" + contentList_temp[i] + "\"})-[r]-(m) return n,m,r").data()
                entity = resultList[0].get('n').get('name')
                if resultList[0].get('n').get('newLabel'):
                    entity_type = resultList[0].get('n').get('newLabel')
                else:
                    entity_type = str(resultList[0].get('n')).split(':')[1].split(' {')[0]
                categoriesList.append(entity_type)
                entityList.append({
                    "entity": entity,
                    "entity_type": entity_type
                })
                for res in resultList:
                    entity1 = res.get('m').get('name')
                    if entity1 in contentList:
                        continue
                    contentList.append(entity1)
                    if res.get('m').get('newLabel'):
                        entity1_type = res.get('m').get('newLabel')
                    else:
                        entity1_type = str(res.get('m')).split(':')[1].split(' {')[0]
                    categoriesList.append(entity1_type)
                    relation = str(res.get('r')).split(':')[1].split(' {')[0]
                    resEntity1 = str(res.get('r')).split(')')[0].split('(')[1]
                    resEntity2 = str(res.get('r')).split('(')[2].split(')')[0]
                    entityList.append({
                        "entity": entity1,
                        "entity_type": entity1_type
                    })
                    relationList.append({
                        "entity1": resEntity1,
                        "entity2": resEntity2,
                        "relation": relation
                    })
            contentList_temp = list(set(contentList))
            contentList_temp.sort(key=contentList.index)
            deepCount += 1
            print(deepCount)
        entityList = distinct(entityList, "entity")
        categoriesList = list(set(categoriesList))
        resultMap = {
            "state":1,
            "entityList": entityList,
            "relationList": relationList,
            "categories": categoriesList
        }
        print(resultMap)
        resultMap = json.dumps(resultMap, ensure_ascii=False)
        return resultMap


def distinct(items, key):
    key = itemgetter(key)
    items = sorted(items, key=key)
    return [next(v) for _, v in groupby(items, key=key)]


if __name__=="__main__":
    # createDB()
    # testInsert()
    # clearDB()
    # maps = {
    #     "entity": "人工智能",
    #     "entity_type": "计算机技术"
    # }
    # updateEntityLabel(maps)
    fuzzySearch("机器")
    searchDB("机器", 1)
    # graph = Graph('http://localhost:7474', username='neo4j', password='root')
    # resultList = graph.run("match (n {name:\"机器学习\"}) return n").data()
    # print(1)
    # neo4jList = [
    #     {
    #         "entity1": "王雅楠",
    #         "entity1_type": "人物",
    #         "entity2": "中国海洋大学",
    #         "entity2_type": "高校",
    #         "relation": "毕业于"
    #     }
    # ]
    # insertRecord(neo4jList)

