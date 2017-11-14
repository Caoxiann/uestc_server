from flask import Flask
from flask import request
from flask import session
from flask import make_response, jsonify, render_template
import uestc

app = Flask('server')
app.secret_key = 'yxh2017'

uestc_sessions = {}


@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    passwd = data.get('passwd')
    print(username, passwd)
    d = uestc.login(username, passwd)
    login_session = d["session"]
    name = d["name"]

    if login_session == 201 or login_session == 202:
        resp = make_response()
        resp.status_code = login_session
        return resp
    else:
        session['username'] = username
        uestc_sessions[username] = login_session
        resp = make_response(name)
        resp.status_code = 200
        return resp


@app.route('/getcourse', methods=['GET'])
def get_course():
    if 'username' in request.args:
        username = request.args.get('username')
        login_session = uestc_sessions.get(username)
        if login_session:
            semester = request.args.get('semester')
            courses = uestc.query.get_course(login_session, semester)
            if courses:
                return jsonify(courses)
            else:
                return "Error occur when getting courses.", 201, {'content-type': 'text/html'}
        else:
            resp = make_response('Please login again.')
            resp.status_code = 202
            return resp

    else:
        resp = make_response('Please login again.')
        resp.status_code = 202
        return resp


@app.route('/getscore', methods=['GET'])
def get_score():
    if 'username' in request.args:
        username = request.args.get('username')
        login_session = uestc_sessions.get(username)
        if login_session:
            semester = request.args.get('semester')
            score = uestc.query.get_score(login_session, semester)
            if score:
                return jsonify(score)
            else:
                return "Error occur when getting score.", 201, {'content-type': 'text/html'}
        else:
            resp = make_response('Please login again.')
            resp.status_code = 202
            return resp
    else:
        resp = make_response('Please login again.')
        resp.status_code = 202
        return resp


@app.route('/getallscore', methods=['GET'])
def get_all_socre():
    if 'username' in request.args:
        username = request.args.get('username')
        login_session = uestc_sessions.get(username)
        if login_session:
            scores = uestc.query.get_all_socre(login_session, username)
            if scores:
                return jsonify(scores)
            else:
                return "Error occur when getting score.", 201, {'content-type': 'text/html'}
        else:
            resp = make_response('Please login again.')
            resp.status_code = 202
            return resp
    else:
        print(uestc_sessions)
        resp = make_response('Please login again.')
        resp.status_code = 202
        return resp


if __name__ == '__main__':
    app.run('0.0.0.0', '6060')


