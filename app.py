import os
from flask import Flask, flash, request, redirect, url_for, Response, jsonify
from werkzeug.utils import secure_filename
from flask import render_template
from pprint import pprint
import linkpred
import json
import networkx as nx
from helpers import formatNetwork, formatNetwork2, getNodefromLabelFromJson
from flask_cors import CORS, cross_origin

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
            newLinks = []
            jsonDict = []

            for authors, score in top.items():
                sentence.append("Il existe une relation thématique et chronologique à exploiter entre : " +
                                str(authors) + "le score  est :" + str(score))
                newLinks.append({
                    "from": getNodefromLabelFromJson(str(authors[0]), initialGraphJson['nodes'])['id'],
                    "to": getNodefromLabelFromJson(str(authors[1]), initialGraphJson['nodes'])['id'],
                    "value": float(1.0)
                })

            # return json.dumps(newLinks)
            # newLinks.append([str(authors[0]), str(authors[1])])
            for authors, score in top.items():
                jsonDict.append({
                    "authorSource": str(authors).split(' - ')[0],
                    "authorDest": str(authors).split(' - ')[0],
                    "score": score
                })
            # responseDict = {"results": jsonDict}
            return render_template('generatedGraph.html', newLinks=newLinks, predictions=sentence, data=initialGraphJson)
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
# @app.route('/file-downloads/')
# def file_downloads():
#     try:
#         return render_template('downloads.html')
#     except Exception as e:
#         return str(e)
