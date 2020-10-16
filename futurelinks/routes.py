import os
from flask import Flask, flash, request, redirect, url_for, Response, jsonify, send_file, abort
from werkzeug.utils import secure_filename
from flask import render_template
from pprint import pprint
import linkpred
import json
import networkx as nx
from futurelinks.helpers import formatNetwork, formatNetwork2, getNodefromLabelFromJson, intersection
from flask_cors import CORS, cross_origin
import math
from dotenv import load_dotenv
from futurelinks.mypred import linkpred as mypred
from futurelinks.forms import RegistrationForm, LoginForm
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime
from futurelinks import app, db, bcrypt
from flask_login import login_user, current_user, logout_user, login_required
from futurelinks.models import User, Stuff
from os.path import join, dirname, realpath
import csv

load_dotenv('.env')

UPLOAD_FOLDER = join(dirname(realpath(__file__)), 'uploadedNets/')

ALLOWED_EXTENSIONS = {'net', 'txt'}
APP_URL = os.environ.get('APP_URl')
# DL_AS_NET_URL = str(os.environ.get('APP_URl')) + '/downloadAsPajet'


cors = CORS(app, resources={r"/foo": {"origins": "*"}})


# login_manager = LoginManager(app)
# login_manager.login_view = 'login'
# login_manager.login_message_category = 'info'


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/graph', methods=['GET', 'POST'])
def graph():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
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

            CommonNeighbours = mypred.predictors.CommonNeighboursGF(
                H, excluded=H.edges())
            CommonNeighbours_results = CommonNeighbours.predict()
            top = CommonNeighbours_results.top()
            sentence = []
            sentenceunsorted = []
            newLinks = []
            jsonDict = []
            # resultsList = []
            G = nx.convert_node_labels_to_integers(H, 1, "default", "label")
            CommonNeighboursG = mypred.predictors.CommonNeighboursGF(
                G, excluded=G.edges())
            CommonNeighbours_resultsG = CommonNeighboursG.predict()
            topG = CommonNeighbours_resultsG.top()
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
            return render_template('generatedGraph.html',
                                   newLinks=newLinks,
                                   predictions=sentence,
                                   data=initialGraphJson,
                                   filename=filename,
                                   DL_AS_NET_URL=DL_AS_NET_URL)
        else:
            flash("format inccorecte, veillez sélectionner un fichier .net valide ")
            return redirect(request.url)
    return render_template('downloads.html')


@app.route('/example')
@cross_origin(origin='localhost', headers=['Content- Type', 'Authorization'])
def example():
    return jsonify(formatNetwork(os.path.join(app.config['UPLOAD_FOLDER'], 'test2.net')))


@app.route('/examplevis')
def examplevis():
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
        source = G.nodes[int(newConnection['from'])]['label']
        target = G.nodes[int(newConnection['to'])]['label']
        H.add_edge(source, target, weight=1.0)
    path = os.path.join(app.config['UPLOAD_FOLDER'],
                        filename+'FutureLinks'+'.net')
    nx.write_pajek(H, path)
    # return jsonify(path)
    return send_file("uploadedNets/"+filename+'FutureLinks'+'.net')


@app.route('/downloadAsCSV', methods=['POST'])
def downloadAsCSV():
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
        source = G.nodes[int(newConnection['from'])]['label']
        target = G.nodes[int(newConnection['to'])]['label']
        H.add_edge(source, target, weight=1.0)
    path = app.config['UPLOAD_FOLDER'] + filename+'FutureLinks'+'.csv'
    nx.write_pajek(H, path)
    return send_file(path)


@app.route('/')
def home():
    return render_template('home.html')


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(
            form.password.data).decode('utf-8')
        user = User(username=form.username.data,
                    email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route("/account")
@login_required
def account():
    return render_template('account.html', title='Account')


@app.route("/upload_graph", methods=['GET', 'POST'])
@login_required
def upload_graph():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # if Stuff.query.filter_by(title=file.filename):
            #     file_save_name = "__" + \
            #         str(current_user.email) + "__" + file.filename
            # else:
            #     file_save_name = str(current_user.email)+"__"+file.filename

            file_save_name = datetime.utcnow().strftime("%Y%d%m%H%m")+filename
            file.save(os.path.join(
                app.config['UPLOAD_FOLDER'], file_save_name))
            originalFile = Stuff(title=file_save_name,
                                 type="net", user=current_user)
            db.session.add(originalFile)
            db.session.commit()
            initialGraphJson = formatNetwork2(os.path.join(
                app.config['UPLOAD_FOLDER'], filename))
            G = linkpred.read_network(os.path.join(
                app.config['UPLOAD_FOLDER'], filename))
            H = G.copy()
            num_loops = nx.number_of_selfloops(G)
            if num_loops:
                H.remove_edges_from(nx.selfloop_edges(G))

            CommonNeighbours = mypred.predictors.CommonNeighboursGF(
                H, excluded=H.edges())
            CommonNeighbours_results = CommonNeighbours.predict()
            top = CommonNeighbours_results.top()
            sentence = []
            sentenceunsorted = []
            newLinks = []
            jsonDict = []
            # resultsList = []
            G = nx.convert_node_labels_to_integers(H, 1, "default", "label")
            CommonNeighboursG = mypred.predictors.CommonNeighboursGF(
                G, excluded=G.edges())
            CommonNeighbours_resultsG = CommonNeighboursG.predict()
            topG = CommonNeighbours_resultsG.top()
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

            return render_template('generatedGraph.html',
                                   newLinks=newLinks,
                                   predictions=sentence,
                                   data=initialGraphJson,
                                   filename=filename)
        else:
            flash("format inccorecte, veillez sélectionner un fichier .net valide ")
            return redirect(request.url)
    return render_template('upload_graph.html', title='Account')


@app.route("/view_file", methods=['GET'])
@login_required
def view_file():
    filename = request.args.get('filename')
    if Stuff.query.filter_by(title=filename).first():
        initialGraphJson = formatNetwork2(os.path.join(
            app.config['UPLOAD_FOLDER'], filename))
        G = linkpred.read_network(os.path.join(
            app.config['UPLOAD_FOLDER'], filename))
        H = G.copy()
        num_loops = nx.number_of_selfloops(G)
        if num_loops:
            H.remove_edges_from(nx.selfloop_edges(G))

        CommonNeighbours = mypred.predictors.CommonNeighboursGF(
            H, excluded=H.edges())
        CommonNeighbours_results = CommonNeighbours.predict()
        top = CommonNeighbours_results.top()
        sentence = []
        sentenceunsorted = []
        newLinks = []
        jsonDict = []
        # resultsList = []
        G = nx.convert_node_labels_to_integers(H, 1, "default", "label")
        CommonNeighboursG = mypred.predictors.CommonNeighboursGF(
            G, excluded=G.edges())
        CommonNeighbours_resultsG = CommonNeighboursG.predict()
        topG = CommonNeighbours_resultsG.top()
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
        for s in sentenceunsorted:
            sentence.append(s['text'])
        for authors, score in top.items():
            jsonDict.append({
                "authorSource": str(authors).split(' - ')[0],
                "authorDest": str(authors).split(' - ')[1],
                "score": cngfScore
            })
        return render_template('viewGraph.html',
                               newLinks=newLinks,
                               predictions=sentence,
                               data=initialGraphJson,
                               filename=filename)
    else:
        abort(404)


@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Stuff.query.get_or_404(post_id)
    if post.user != current_user:
        abort(403)
    os.remove(post.getPath())
    db.session.delete(post)
    db.session.commit()
    flash('Le fichier a bien été supprimé', 'success')
    return redirect(url_for('account'))


if __name__ == "__main__":
    app.run(debug=True)
