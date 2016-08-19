"""
All tournament interactions.
"""
import json
import jsonpickle
from flask import Blueprint, g, request
from sqlalchemy.exc import IntegrityError

from controllers.request_helpers import enforce_request_variables, \
json_response, text_response
from models.dao.db_connection import db
from models.dao.registration import TournamentRegistration
from models.dao.tournament import Tournament as TournamentDAO
from models.dao.tournament_round import TournamentRound
from models.tournament import Tournament

TOURNAMENT = Blueprint('TOURNAMENT', __name__)

@TOURNAMENT.url_value_preprocessor
# pylint: disable=unused-argument
def get_tournament(endpoint, values):
    """Retrieve tournament_id from URL and ensure the tournament exists"""
    g.tournament_id = values.pop('tournament_id', None)
    if g.tournament_id:
        g.tournament = Tournament(g.tournament_id)

@TOURNAMENT.route('', methods=['POST'])
@text_response
@enforce_request_variables('inputTournamentName', 'inputTournamentDate')
def add_tournament():
    # pylint: disable=undefined-variable

    """
    POST to add a tournament
    Expects:
        - inputTournamentName - Tournament name. Must be unique.
        - inputTournamentDate - Tournament Date. YYYY-MM-DD
    """
    tourn = Tournament(
        inputTournamentName,
        creator=request.authorization.username)
    tourn.add_to_db(inputTournamentDate)
    return '<p>Tournament Created! You submitted the following fields:</p> \
        <ul><li>Name: {}</li><li>Date: {}</li></ul>'.\
        format(inputTournamentName, inputTournamentDate)

@TOURNAMENT.route('/<tournament_id>/missions', methods=['GET'])
def list_missions():
    """GET list of missions for a tournament."""
    return jsonpickle.encode(
        [x.mission for x in g.tournament.get_dao().rounds.order_by('ordering')],
        unpicklable=False)

@TOURNAMENT.route('/<tournament_id>/score_categories', methods=['GET'])
@json_response
def list_score_categories():
    """
    GET the score categories set for the tournament.
    e.g. [{ 'name': 'painting', 'percentage': 20, 'id': 2 }]
    """
    return [{
        'id':             x.id,
        'name':           x.name,
        'percentage':     x.percentage,
        'per_tournament': x.per_tournament,
        'min_val':        x.min_val,
        'max_val':        x.max_val
    } for x in g.tournament.list_score_categories()]

@TOURNAMENT.route('/', methods=['GET'])
@json_response
def list_tournaments():
    """
    GET a list of tournaments
    Returns json. The only key is 'tournaments' and the value is a list of
    tournament names
    """
    # pylint: disable=no-member
    details = [
        {'name': x.name, 'date': x.date, 'rounds': x.num_rounds}
        for x in TournamentDAO.query.all()]

    return {'tournaments' : details}

@TOURNAMENT.route('/<tournament_id>/register', methods=['POST'])
@text_response
@enforce_request_variables('inputUserName')
def register():
    # pylint: disable=undefined-variable

    """
    POST to apply for entry to a tournament.
    Expects:
        - inputUserName - Username of player applying
    """
    rego = TournamentRegistration(inputUserName, g.tournament_id)
    rego.clashes()

    try:
        db.session.add(rego)
        db.session.commit()
    except IntegrityError:
        raise ValueError("Check username and tournament")

    return 'Application Submitted'

@TOURNAMENT.route('/<tournament_id>/missions', methods=['POST'])
@text_response
@enforce_request_variables('missions')
def set_missions():
    # pylint: disable=undefined-variable

    """POST to set the missions for a tournament.A list of strings expected"""
    rounds = g.tournament.details()['rounds']
    try:
        json_missions = json.loads(missions)
    except TypeError:
        json_missions = missions

    if len(json_missions) != int(rounds):
        raise ValueError('Tournament {} has {} rounds. \
            You submitted missions {}'.\
            format(g.tournament_id, rounds, missions))

    for i, mission in enumerate(json_missions):
        rnd = g.tournament.get_round(i + 1)
        # pylint: disable=no-member
        rnd.mission = mission if mission else \
            TournamentRound.__table__.c.mission.default.arg
        db.session.add(rnd)

    db.session.commit()
    return 'Missions set: {}'.format(missions)

@TOURNAMENT.route('/<tournament_id>/score_categories', methods=['POST'])
@text_response
@enforce_request_variables('categories')
def set_score_categories():
    # pylint: disable=undefined-variable

    """
    POST to set tournament categories en masse
    """
    new_categories = []
    try:
        cats = json.loads(categories)
    except TypeError:
        cats = categories

    for json_cat in cats:
        try:
            cat = json.loads(request.values.get(json_cat, []))
        except TypeError:
            cat = request.get_json().get(json_cat)

        new_categories.append({
            'name':       cat[0],
            'percentage': cat[1],
            'per_tourn':  cat[2],
            'min_val':    cat[3],
            'max_val':    cat[4]})

    g.tournament.set_score_categories(new_categories)

    return 'Score categories set: {}'.\
        format(', '.join([str(cat['name']) for cat in new_categories]))

@TOURNAMENT.route('/<tournament_id>', methods=['GET'])
@json_response
def tournament_details():
    """
    GET to get details about a tournament. This includes entrants and format
    information
    """
    return g.tournament.details()
