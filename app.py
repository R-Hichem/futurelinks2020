import os
from flask import Flask, flash, request, redirect, url_for, Response, jsonify, send_file
from werkzeug.utils import secure_filename
from flask import render_template
from pprint import pprint
import linkpred
import json
import networkx as nx
from helpers import formatNetwork, formatNetwork2, getNodefromLabelFromJson, intersection
from flask_cors import CORS, cross_origin
import math

UPLOAD_FOLDER = 'uploadedNets/'
ALLOWED_EXTENSIONS = {'net', 'txt'}


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = '3d6f45a5fc12445dbac2f59c3b6c7cb1'
app.config['CORS_HEADERS'] = 'Content-Type'

cors = CORS(app, resources={r"/foo": {"origins": "*"}})


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        # return Response(file).get_data()
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            # return redirect(url_for('uploaded_file',filename=filename))
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            initialGraphJson = formatNetwork2(os.path.join(
                app.config['UPLOAD_FOLDER'], filename))
            G = linkpred.read_network(os.path.join(
                app.config['UPLOAD_FOLDER'], filename))

            H = G.copy()

            num_loops = nx.number_of_selfloops(G)
            if num_loops:
                H.remove_edges_from(nx.selfloop_edges(G))

            CommonNeighbours = linkpred.predictors.CommonNeighbours(
                H, excluded=H.edges())
            CommonNeighbours_results = CommonNeighbours.predict()
            top = CommonNeighbours_results.top()
            sentence = []
            sentenceunsorted = []
            newLinks = []
            jsonDict = []
            # resultsList = []
            G = nx.convert_node_labels_to_integers(H, 1, "default", "label")

            CommonNeighboursG = linkpred.predictors.CommonNeighbours(
                G, excluded=G.edges())

            CommonNeighbours_resultsG = CommonNeighboursG.predict()

            topG = CommonNeighbours_resultsG.top(10)

            # for authors, score in top.items():
            #     sentence.append(
            #         str(authors) + "  le score  est :" + str(score))
            #     newLinks.append({
            #         "from": getNodefromLabelFromJson(str(authors[0]), initialGraphJson['nodes'])['id'],
            #         "to": getNodefromLabelFromJson(str(authors[1]), initialGraphJson['nodes'])['id'],
            #         "value": float(1.0)
            #     })

            for authors, score in topG.items():
                authorsArray = [authors[0], authors[1]]
                common = intersection(
                    list(G.neighbors(authors[0])), list(G.neighbors(authors[1]))) + authorsArray
                subG = G.subgraph(common)
                cngfScore = 0
                for nodeID, nodeInfo in subG.nodes(data=True):

                    if nodeID not in authorsArray:
                        cngfScore = cngfScore + \
                            (subG.degree[nodeID] /
                             math.log10(G.degree[nodeID]))

                authorOne = G.nodes[authorsArray[1]]
                authorTwo = G.nodes[authorsArray[0]]
                sentenceunsorted.append({
                    "text": authorOne['label'] + " - " + authorTwo['label'] +
                    "  le score  est :" + str(cngfScore),
                    "score": cngfScore
                })
                newLinks.append({
                    "from": authorOne['id'],
                    "to": authorTwo['id'],
                    "value": float(1.0),
                    "authOne": authorOne,
                    "authTwo": authorTwo,
                    "score": cngfScore
                })

            # return json.dumps(newLinks)
            # newLinks.append([str(authors[0]), str(authors[1])])

            newLinks = sorted(newLinks, key=lambda i: i['score'], reverse=True)
            sentenceunsorted = sorted(
                sentenceunsorted, key=lambda i: i['score'], reverse=True)
            for s in sentenceunsorted:
                sentence.append(s['text'])
            for authors, score in top.items():
                jsonDict.append({
                    "authorSource": str(authors).split(' - ')[0],
                    "authorDest": str(authors).split(' - ')[1],
                    "score": cngfScore
                })
            # responseDict = {"results": jsonDict}
            # return json.dumps(newLinks)
            return render_template('generatedGraph.html', newLinks=newLinks, predictions=sentence, data=initialGraphJson, filename=filename)
        else:
            flash("format inccorecte, veillez sélectionner un fichier .net valide ")
            return redirect(request.url)
    return render_template('downloads.html')


@app.route('/example')
@cross_origin(origin='localhost', headers=['Content- Type', 'Authorization'])
def graphExample():
    return jsonify(formatNetwork(os.path.join(app.config['UPLOAD_FOLDER'], 'test2.net')))


@app.route('/examplevis')
def visGraph():
    return render_template('vis.html')


@app.route('/downloadAsPajet', methods=['POST'])
def downloadAsPajet():
    data = request.json["data"]
    filename = data['filename']
    G = linkpred.read_network(os.path.join(
        app.config['UPLOAD_FOLDER'], filename))

    H = G.copy()

    num_loops = nx.number_of_selfloops(G)
    if num_loops:
        H.remove_edges_from(nx.selfloop_edges(G))

    G = nx.convert_node_labels_to_integers(H, 1, "default", "label")

    for newConnection in data['newConnections']:
        G.add_edge(newConnection['from'], newConnection['to'], weight=1.0)

    path = app.config['UPLOAD_FOLDER'] + filename+'FutureLinks'+'.net'
    nx.write_pajek(G, path)
    return send_file(path)


# @app.route('/file-downloads/')
# def file_downloads():
#     try:
#         return render_template('downloads.html')
#     except Exception as e:
#         return str(e)
