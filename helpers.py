import re


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


# print(nodes[0])

# for line in netfile.readline():
#     print(line.split)

# result = [line.split('*Arcs') for line in netfile.readlines()]
# print(result[331])
