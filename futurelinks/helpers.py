import re
import networkx as nx
import linkpred
import json


def formatNetwork(filePath):
    netfile = open(filePath, 'r')
    fileArray = netfile.readlines()
    nodesSize = int(fileArray[0].split(' ')[1])
    nodes = fileArray[1:nodesSize]
    edges = fileArray[nodesSize+2:len(fileArray)-1]
    jsonNodeArray = []
    jsonEdgeArray = []
    for node in nodes:
        authorName = re.findall(r'"([^"]*)"', node)[0]
        authorId = node.split(' ')[0]
        jsonNodeArray.append({
            "id": int(authorId),
            "label": authorName
        })
    for edge in edges:
        edgeList = edge.split(' ')
        jsonEdgeArray.append({
            "from": int(edgeList[0]),
            "to": int(edgeList[1]),
            "value": float(edgeList[2])
        })
    jsonNetwork = {
        "nodes": jsonNodeArray,
        "edges": jsonEdgeArray,
    }
    return jsonNetwork


def formatNetwork2(filePath):
    network = linkpred.read_network(filePath)
    G = nx.convert_node_labels_to_integers(network, 1, "default", "label")
    jsonNodeArray = []
    jsonEdgeArray = []
    for node in json.loads(nx.jit_data(G)):
        authorName = node['data']['label']
        authorId = node['data']['id']
        jsonNodeArray.append({
            "id": int(authorId),
            "label": authorName
        })
        if 'adjacencies' in node:
            edges = node['adjacencies']
            for edge in edges:
                jsonEdgeArray.append({
                    "from": int(authorId),
                    "to": int(edge['nodeTo']),
                    "value": int(edge['data']['weight']),
                    "edgeID": str(authorId)+'to'+str(edge['nodeTo'])
                })
    jsonNetwork = {
        "nodes": jsonNodeArray,
        "edges": jsonEdgeArray,
    }
    return jsonNetwork


def getNodefromLabelFromJson(string, nodesList):
    return next((x for x in nodesList if x['label'] == string), None)


def getSubGraphNodes(G, nodeOne, nodeTwo):
    paths_between_generator = nx.all_simple_paths(
        G=G, source=nodeOne, target=nodeTwo)
    nodes_between_set = {
        node for path in paths_between_generator for node in path}
    SG = G.subgraph(nodes_between_set)
    return SG


def intersection(lst1, lst2):
    lst3 = [value for value in lst1 if value in lst2]
    return lst3
