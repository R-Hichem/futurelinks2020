import os
from flask import Flask, flash, request, redirect, url_for, Response, jsonify, send_file, abort, send_from_directory
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
UPLOAD_FOLDER_CSV = join(dirname(realpath(__file__)), 'uploadedCsv/')

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


def isCsv(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {"csv"}


@app.route('/graph', methods=['GET', 'POST'])
def graph():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('Veillez choisir un fichier')
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
    #csv_path = os.path.join(app.config['UPLOAD_FOLDER'], filename+".csv")
    return send_file("uploadedNets/" + filename + '.csv')


@app.route('/fetchCSV', methods=['POST'])
def fetchCSV():
    data = request.json["data"]
    filename = data['filename']
    return send_file("uploadedNets/"+filename)


@app.route('/')
def home():
    return render_template('home.html',  user=current_user)


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(
            form.password.data).decode('utf-8')
        if(User.query.count() > 0):
            newID = User.query.all()[-1].id + 1
        else:
            newID = 1
        user = User(username=form.username.data,
                    email=form.email.data, password=hashed_password, id=newID)
        db.session.add(user)
        db.session.commit()
        flash('Votre compte a bien été crée ! Vous pouvez vous connecter', 'success')
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
            flash(
                'Informations de Connexion incorrecte, veuillez vérifier vos identifiants', 'danger')
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
            flash('No file part', 'netErrors')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('Veillez choisir un fichier', 'netErrors')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_save_name = datetime.utcnow().strftime("%Y_%d_%m_%H_%M_%S_")+filename
            file_path = os.path.join(
                app.config['UPLOAD_FOLDER'], file_save_name)
            file.save(file_path)
            if(Stuff.query.count() > 0):
                newID = Stuff.query.all()[-1].id + 1
            else:
                newID = 1
            originalFile = Stuff(title=file_save_name,
                                 type="net", user=current_user, id=newID)
            db.session.add(originalFile)
            initialGraphJson = formatNetwork2(file_path)
            G = linkpred.read_network(file_path)
            H = G.copy()
            num_loops = nx.number_of_selfloops(G)
            if num_loops:
                H.remove_edges_from(nx.selfloop_edges(G))

            CommonNeighbours = mypred.predictors.CommonNeighboursGF(
                H, excluded=H.edges())
            CommonNeighbours_results = CommonNeighbours.predict()
            top = CommonNeighbours_results.top()
            topAll = CommonNeighbours_results.top(0)
            sentence = []
            sentenceunsorted = []
            newLinks = []
            jsonDict = []
            # resultsList = []
            G = nx.convert_node_labels_to_integers(H, 1, "default", "label")
            CommonNeighboursG = mypred.predictors.CommonNeighboursGF(
                G, excluded=G.edges())
            CommonNeighbours_resultsG = CommonNeighboursG.predict()
            topG = CommonNeighbours_resultsG.top(13)
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
                    "score":  float("{:.4f}".format(cngfScore))
                })
            for s in sentenceunsorted:
                sentence.append(s['text'])
            for authors, score in topAll.items():
                jsonDict.append({
                    "authorSource": str(authors).split(' - ')[0].encode("utf-8"),
                    "authorDest": str(authors).split(' - ')[1].encode("utf-8"),
                    "score": score
                })

            # responseDict = {"results": jsonDict}
            # return json.dumps(newLinks)
            csv_columns = ['authorSource', 'authorDest', 'score']
            csv_file = file_path+".csv"
            try:
                with open(csv_file, 'w') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
                    writer.writeheader()
                    for data in jsonDict:
                        writer.writerow(data)
                if(Stuff.query.count() > 0):
                    newID = Stuff.query.all()[-1].id + 1
                else:
                    newID = 1
                CSV_results = Stuff(title=file_save_name +
                                    ".csv", type="csv", user=current_user, id=newID)
                db.session.add(CSV_results)
            except IOError:
                print("I/O error")
            db.session.commit()
            return render_template('generatedGraph.html',
                                   newLinks=newLinks,
                                   predictions=sentence,
                                   data=initialGraphJson,
                                   filename=file_save_name)
        else:
            flash(
                "format inccorecte, veillez sélectionner un fichier .net valide ", 'netErrors')
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
                "score": float("{:.2f}".format(cngfScore))
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


@app.route("/upload_csv", methods=['POST'])
@login_required
def upload_csv():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'netErrors')
            return redirect("/upload_graph")
        file = request.files['file']
        if file.filename == '':
            flash('Veillez choisir un fichier', 'netErrors')
            return redirect("/upload_graph")
        if file and isCsv(file.filename):
            try:
                filename = secure_filename(file.filename)
                file.save(os.path.join(
                    app.config['UPLOAD_FOLDER_CSV'], filename))
                G = nx.read_adjlist(os.path.join(app.config['UPLOAD_FOLDER_CSV'], filename),
                                    create_using=nx.DiGraph, delimiter=";")
                nx.write_pajek(G, os.path.join(
                    app.config['UPLOAD_FOLDER_CSV'], filename + ".net"))
                # return jsonify({'path': os.path.join(
                #     app.config['UPLOAD_FOLDER_CSV'], filename + ".net")})
                try:
                    network = nx.read_pajek(os.path.join(
                        app.config['UPLOAD_FOLDER_CSV'], filename + ".net"))
                except:
                    flash("CSV non valide !", 'netErrors')
                    return redirect("/upload_graph")
                return send_file("uploadedCsv/" + filename + ".net", mimetype="text/csv", as_attachment=True)
            except:
                flash("CSV non valide !", 'netErrors')
                return redirect("/upload_graph")
        else:
            flash(
                "format inccorecte, veillez sélectionner un fichier .csv valide ", 'netErrors')
            return redirect("/upload_graph")
    return render_template('upload_csv.html', title='Account')


if __name__ == "__main__":
    app.run(debug=True)
