from flask import Flask, render_template, request, session, url_for, redirect
from werkzeug.utils import secure_filename
import mysql.connector
from operator import is_not
from functools import partial
import os
import datetime

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "upload")
ML_MODELS = os.path.join(os.path.dirname(__file__), "ml/models")
ALLOWED_EXTENSIONS = set(['csv'])

# create a server instance
app = Flask(__name__, static_url_path="/static", static_folder=os.path.join(os.path.dirname(__file__), "static"))
app.secret_key = '222'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def getConnection():
    connection = mysql.connector.connect(host="127.0.0.1", user="root", password="NehalBandal@84", database="fifa18")
    return connection


def registerManager(connection, cursor, name, club, password, email):
    query = "INSERT INTO manager VALUES('{0}','{1}','{2}','{3}')".format(name, email, club, password)
    cursor.execute(query)
    connection.commit()
    connection.close()


def verifyManager(connection, cursor, email, password):
    query = "SELECT * FROM manager where email='{0}' and password='{1}'".format(email, password)
    cursor.execute(query)
    managerRecord = cursor.fetchone()
    return managerRecord


def getClubs(connection, cursor):
    query = "SELECT DISTINCT Club FROM player_personal_info"
    cursor.execute(query)
    clublist = cursor.fetchall()
    clubs = []
    for c in clublist:
        clubs.append(c[0])
    return clubs


def getPlayerList(connection, cursor, team):
    query = """SELECT y.Name, y.Age, x.Position, x.Overall FROM player_abstract_info x INNER JOIN player_personal_info y ON x.ID = y.ID WHERE y.Club='{0}' """.format(team)
    cursor.execute(query)
    squadlist = cursor.fetchall()
    return squadlist

def removePlayer(player, squadlist):
    for p in squadlist:
        if p == player:
            squadlist.remove(p)


def getSquad(connection, cursor, team, formation):
    squadlist = getPlayerList(connection, cursor, team)
    finalXI = []
    for pos in formation:
        inner = []
        posList = pos.split('|')
        for p in posList:
            for player in squadlist:
                if player[2] == p:
                    inner.append(player)
        inner = list(filter(partial(is_not, None), inner))
        if len(inner) >= 1:
            player = max(inner, key=lambda item: item[3])
            finalXI.append(player)
            squadlist.remove(player)
        else:
            finalXI.append(pos + " Not available")
    return finalXI


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def updateFileLocation(connection, cursor, name):
    query = "INSERT INTO uploaded_files VALUES('{0}','{1}')".format(datetime.datetime.now(), name)
    cursor.execute(query)
    connection.commit()
    connection.close()


@app.route("/", methods=['GET', 'POST'])
def registration():
    connection = getConnection()
    cursor = connection.cursor()
    if request.method == "POST":
        name = request.form.get("name")
        club = request.form.get("club")
        password = request.form.get("passwd")
        email = request.form.get("email")
        registerManager(connection, cursor, name, club, password, email)
        return redirect(url_for("login"))
    else:
        clublist = getClubs(connection, cursor)
        return render_template("registration.html", clubs=clublist)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method=="POST":
        print("form submitted")
        email =request.form.get('email')
        password = request.form.get('passwd')
        connection = getConnection()
        cursor = connection.cursor()
        managerRecord = verifyManager(connection, cursor, email, password)
        if len(managerRecord) > 0:
            session['is_logged_in'] = True
            name = managerRecord[0]
            club = managerRecord[2]
            session['team'] = club
            session['name'] = name
            return render_template("home.html", name=name, club=club)
        else:
            print("login failed.")
            return redirect(url_for("login"))
    else:
        return render_template("login.html")

@app.route('/teamManagement', methods=['GET', 'POST'])
def teamManagement():
    connection = getConnection()
    cursor = connection.cursor()
    #    team='FC Barcelona'
    form_442_adj = ['GK', 'LB|LWB', 'CB|LCB|RCB', 'CB|LCB|RCB', 'RB|RWB', 'CM|CAM|CDM', 'CM|CAM|CDM',
                    'LM|LCM|LW|LAM', 'RM|RCM|RW|RAM', 'ST|CF|RF|LF', 'ST|CF|RF|LF']
    squadlist = getPlayerList(connection, cursor, session['team'])
    finalXI = getSquad(connection, cursor, session['team'], form_442_adj)
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            return render_template("TeamManagement.html", data=squadlist, squad=finalXI)

        file = request.files['file']

        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            return "<script type=\"text/javascript\">alert(\"Enter valid file\"); window.location.href=\"http://127.0.0.1:5000/teamManagement\"</script>"

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            name = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            name = name.replace("\\", "\\\\")
            print("file name: ", name)
            updateFileLocation(connection, cursor, name)
            path = os.path.join(os.path.dirname(__file__))+"/end_to_end_upload.py"
            status = os.system("python {}".format(path))
            if status == 0:
                return "<script type=\"text/javascript\">alert(\"New Data Added successfully...\"); window.location.href=\"http://127.0.0.1:5000/teamManagement\"</script>"
            else:
                return "<script type=\"text/javascript\">alert(\"Upload Fail...\"); window.location.href=\"http://127.0.0.1:5000/teamManagement\"</script>"

    return render_template("TeamManagement.html", data=squadlist, squad=finalXI, club=session['team'])


@app.route('/analysis')
def analysis():
    return render_template("Analysis.html")

@app.route('/wfa')
def wfa():
    return render_template("Analysis/wfa.html")


@app.route('/playerWorth')
def playerWorth():
    return render_template("Analysis/playerWorth.html")


@app.route('/clubProfile')
def clubProfile():
    return render_template("Analysis/clubProfile.html")


@app.route('/attributeAnalysis')
def attributeAnalysis():
    return render_template("Analysis/attributeAnalysis.html")


@app.route("/logout")
def logout():
    return redirect(url_for("login"))


app.run(debug=True)
