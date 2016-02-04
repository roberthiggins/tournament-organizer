"""
Module for storing games.

A game is simply a match between two entries. It is played on a table.
"""

from db_connections.db_connection import db_conn
from db_connections.entry_db import Entry

@db_conn()
# pylint: disable=E0602
def get_game_from_score(entry_id, score_key):
    """Given an entry and score_key, you should be able to work out the game"""
    cur.execute(
        "SELECT tournament, for_round, entry_id \
        FROM player_score WHERE entry_id = %s AND key = %s",
        [entry_id, score_key])
    tournament_round_entry = cur.fetchone()

    if tournament_round_entry is None:
        return None

    cur.execute(
        "SELECT g.id, g.table_num, g.protected_object_id \
        FROM game g INNER JOIN game_entrant e ON g.id = e.game_id \
        WHERE g.tourn = %s AND g.round_num = %s AND e.entrant_id = %s",
        tournament_round_entry)
    game_id_table = cur.fetchone()

    cur.execute(
        "SELECT entrant_id FROM game_entrant WHERE game_id = %s",
        [game_id_table[0]])
    entrants = [Entry(entry_id=x[0]) for x in cur.fetchall()]
    if len(entrants) == 1:
        entrants.append('BYE')

    return Game(entrants,
                game_id=game_id_table[0],
                tournament_id=tournament_round_entry[0],
                round_id=tournament_round_entry[1],
                table_number=game_id_table[1],
                protected_object_id=tournament_round_entry[2])

# pylint: disable=E0602
class Game(object):
    """
    Representation of a single match between entrants.
    This might be a BYE
    """

    #pylint: disable=R0913
    def __init__(self, entrants, game_id=None, tournament_id=None,
                 round_id=None, table_number=None, protected_object_id=None):
        self.game_id = game_id
        self.tournament_id = tournament_id
        self.round_id = round_id
        self.table_number = table_number
        self.entry_1 = None if entrants[0] == 'BYE' else entrants[0].entry_id
        self.entry_2 = None if entrants[1] == 'BYE' else entrants[1].entry_id
        self.protected_object_id = protected_object_id


    @db_conn(commit=True)
    def write_to_db(self):
        """Write a game to db"""

        # Get a protected_object_id
        cur.execute("INSERT INTO protected_object VALUES(DEFAULT) RETURNING id")
        protected_object_id = cur.fetchone()[0]

        cur.execute(
            "INSERT INTO game \
            VALUES(DEFAULT, %s, %s, %s, %s) RETURNING *",
            [
                self.round_id,
                self.tournament_id,
                self.table_number,
                protected_object_id
            ]
        )
        game = cur.fetchone()
        self.game_id = game[0]
        self.protected_object_id = game[4]

        if self.entry_1 is not None:
            cur.execute(
                "INSERT INTO game_entrant VALUES(%s, %s)",
                [self.game_id, self.entry_1])
        if self.entry_2 is not None:
            cur.execute(
                "INSERT INTO game_entrant VALUES(%s, %s)",
                [self.game_id, self.entry_2])
