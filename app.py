import os
from flask import Flask, flash, request, redirect, url_for, Response, jsonify
from werkzeug.utils import secure_filename
from flask import render_template
from pprint import pprint
import linkpred
import json
import networkx as nx
from helpers import formatNetwork

UPLOAD_FOLDER = 'uploadedNets/'
ALLOWED_EXTENSIONS = {'net', 'txt'}


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = '3d6f45a5fc12445dbac2f59c3b6c7cb1'


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
            G = linkpred.read_network(os.path.join(
                app.config['UPLOAD_FOLDER'], filename))

            H = G.copy()

            num_loops = nx.number_of_selfloops(G)

            if num_loops:
                H.remove_edges_from(nx.selfloop_edges(G))
                return 'oui'

            CommonNeighbours = linkpred.predictors.CommonNeighbours(
                H, excluded=H.edges())
            CommonNeighbours_results = CommonNeighbours.predict()
            top = CommonNeighbours_results.top()
            # sentence = ''
            # for authors, score in top.items():
            #     sentence = sentence + ("Il existe une relation thématique et chronologique à exploiter entre : \n" + str(authors) + "\n" + "le score (indice de confiance) est :\n" +
            #                            str(score) + "\n" + "Plus la valeur est supérieure à 1.0 plus la possibilitée de relation entre ces auteurs est forte\n")
            jsonDict = []
            for authors, score in top.items():
                jsonDict.append({
                    "authorSource": str(authors).split(' - ')[0],
                    "authorDest": str(authors).split(' - ')[0],
                    "score": score
                })
            # responseDict = {"results": jsonDict}
            return jsonify(formatNetwork(os.path.join(app.config['UPLOAD_FOLDER'], filename)))
            return jsonify(jsonDict)
    return render_template('downloads.html')


@app.route('/example')
def graphExample():
    return jsonify(formatNetwork(os.path.join(app.config['UPLOAD_FOLDER'], 'test2.net')))

# @app.route('/file-downloads/')
# def file_downloads():
#     try:
#         return render_template('downloads.html')
#     except Exception as e:
#         return str(e)
