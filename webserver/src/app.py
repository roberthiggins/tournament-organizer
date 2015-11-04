import datetime
import os
import re
import yaml

from flask import Flask, render_template, request, json, make_response

from player_db import PlayerDBConnection
from tournament_db import TournamentDBConnection
from registration_db import RegistrationDBConnection

app                     = Flask(__name__)
player_db_conn          = PlayerDBConnection()
tournament_db_conn      = TournamentDBConnection()
registration_db_conn    = RegistrationDBConnection()

# Page rendering
@app.route("/")
def main():
    return render_template('index.html')

@app.route('/createtournament')
def showCreateTournament():
    return render_template('create-a-tournament.html')

@app.route('/feedback')
def showPlaceFeedback():
    return render_template('feedback.html', title='Place Feedback', intro='Please give us feedback on your experience on the site')

@app.route('/registerforatournament')
def showRegisterForTournament():
    return render_template('register-for-tournament.html', tournaments=tournament_db_conn.listTournaments())

@app.route('/signup')
def showAddPlayer():
    return render_template('create-a-player.html')

@app.route('/suggestimprovement')
def showSuggestImprovement():
    return render_template('feedback.html', title='Suggest Improvement', intro='Suggest a feature you would like to see on the site')

# Page actions
@app.route('/registerfortournament', methods=['POST'])
def applyForTournament():
    _userName = request.form['inputUserName']
    _tournamentName = request.form['inputTournamentName']

    if not _userName or not _tournamentName:
        return make_response("Enter the required fields", 400)

    try:
        return make_response(
                registration_db_conn.registerForTournament(
                    _tournamentName,
                    _userName),
                200)
    except Error as e:
        return make_response(e, 200)


@app.route('/addTournament', methods=['POST'])
def addTournament():
    _name = request.form['inputTournamentName']
    _date = request.form['inputTournamentDate']

    if not _name or not _date:
        return make_response("Please fill in the required fields", 400)

    try:
        _date = datetime.datetime.strptime(
                    request.form['inputTournamentDate'],
                    "%Y-%m-%d")
        assert _date.date() >= datetime.date.today()
    except Exception as e:
        return make_response("Enter a valid date", 400)

    try:
        if tournament_db_conn.tournamentExists(_name):
            return make_response("A tournament with name %s already exists! Please choose another name" % _name, 400)
        tournament_db_conn.addTournament({'name' : _name, 'date' : _date})
        return make_response('<p>Tournament Created! You submitted the following fields:</p><ul><li>Name: {_name}</li><li>Date: {_date}</li></ul>'.format(**locals()), 200)
    except Error as e:
        return make_response(e, 500)


@app.route('/addPlayer', methods=['POST'])
def addPlayer():
    _user_name = request.form['inputUsername']
    _email = request.form['inputEmail']
    _password = request.form['inputPassword']
    _confirmPassword = request.form['inputConfirmPassword']

    if not _user_name or not _email:
        return make_response("Please fill in the required fields", 400)

    if not _password or not _confirmPassword or _password != _confirmPassword:
        return make_response("Please enter two matching passwords", 400)

    try:
        if player_db_conn.usernameExists(_user_name):
            return make_response("A user with the username %s already exists! Please choose another name" % _user_name, 400)

        player_db_conn.addAccount({'user_name': _user_name, 'email' : _email, 'password': _password})
        return make_response('<p>Account created! You submitted the following fields:</p><ul><li>User Name: {_user_name}</li><li>Email: {_email}</li></ul>'.format(**locals()), 200)
    except Error as e:
        return make_response(e, 500)

@app.route('/placefeedback', methods=['POST'])
def placeFeedback():
    _feedback = request.form['inputFeedback'].strip('\s\n\r\t\+')
    if re.match( r'^[\+\s]*$', _feedback) is not None:
        return make_response("Please fill in the required fields", 400)
    return make_response("Thanks for you help improving the site", 200)


if __name__ == "__main__":
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

