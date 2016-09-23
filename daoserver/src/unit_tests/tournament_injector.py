"""
An injector to create tournaments for unit tests

If you want to check that this has cleaned up after itself you can run db-usage
or something similar to:

    SELECT schemaname,relname,n_live_tup
    FROM pg_stat_user_tables
    ORDER BY n_live_tup DESC;

"""
# pylint: disable=no-member

from datetime import datetime, timedelta

from models.dao.account import Account
from models.dao.db_connection import db
from models.dao.permissions import AccountProtectedObjectPermission, \
ProtectedObject, ProtObjAction, ProtObjPerm
from models.dao.registration import TournamentRegistration as TReg
from models.dao.tournament import Tournament
from models.dao.tournament_entry import TournamentEntry as Entry
from models.dao.tournament_round import TournamentRound

from models.permissions import PermissionsChecker, PERMISSIONS, \
set_up_permissions

class TournamentInjector(object):
    """Insert a tournament using the ORM. You can delete them as well"""

    def __init__(self):
        self.tournament_ids = set()
        self.tournament_names = set()
        self.accounts = set()
        self.existing_perms = set([o.id for o in ProtObjAction.query.all()])
        set_up_permissions()

    def inject(self, name, rounds=0, num_players=6, date=None):
        """Create a tournament and inkect it into the db."""

        # To avoid clashes we shift default tournament into the future
        if date is None:
            date = datetime.now() + timedelta(weeks=len(self.tournament_ids))

        self.create_tournament(name, date, rounds)

        self.create_players(name, num_players)

        return

    def delete(self):
        """Remove all tournaments we have injected"""

        self.delete_scores()

        from models.tournament import Tournament as Tourn
        for tourn in self.tournaments().all():
            Tourn(tourn.name).set_number_of_rounds(0)

        self.delete_accounts()

        self.delete_tournaments()

        if len(self.existing_perms):
            ProtObjAction.query.\
                filter(~ProtObjAction.id.in_(self.existing_perms)).\
                delete(synchronize_session=False)
            self.existing_perms = set()

        db.session.commit()
        return

    def add_player(self, tournament_name, username, email='foo@bar.com'):
        """Create player account and enter them"""
        db.session.add(Account(username, email))
        db.session.flush()
        db.session.add(Entry(username, tournament_name))
        db.session.flush()
        self.accounts.add(username)

    def add_round(self, tourn_name, round_num, mission):
        """Add a TournamentRound. Caller's job to ensure clash avoidance"""
        db.session.add(TournamentRound(tourn_name, int(round_num), mission))

    def create_tournament(self, name, date, rounds=0):
        """Create a tournament"""
        creator_name = '{}_creator'.format(name)
        db.session.add(Account(creator_name, '{}@bar.com'.format(creator_name)))
        db.session.flush()

        tourn = Tournament(name)
        tourn.num_rounds = rounds
        tourn.date = date
        tourn.creator_username = creator_name
        db.session.add(tourn)
        db.session.flush()
        self.tournament_ids.add(tourn.id)
        self.tournament_names.add(tourn.name)

        PermissionsChecker().add_permission(
            creator_name,
            PERMISSIONS['ENTER_SCORE'],
            tourn.protected_object)

    def create_players(self, tourn_name, num_players):
        """Create some accounts and enter them in the tournament"""
        for entry_no in range(1, num_players + 1):
            play_name = '{}_player_{}'.format(tourn_name, entry_no)
            db.session.add(Account(play_name, '{}@test.com'.format(play_name)))
            db.session.flush()
            db.session.add(Entry(play_name, tourn_name))
            db.session.flush()
            self.accounts.add(play_name)

    def delete_accounts(self):
        """Delete user accounts and sundry we have injected"""
        if not len(self.accounts):
            return

        # Some relations can't be deleted via relationship for some reason
        # registrations and entries
        if len(self.tournament_ids):
            TReg.query.filter(TReg.tournament_id.in_(self.tournament_ids)).\
                delete(synchronize_session=False)
        if len(self.tournament_names):
            Entry.query.filter(Entry.tournament_id.in_(self.tournament_names)).\
                delete(synchronize_session=False)

        # Accounts
        AccountProtectedObjectPermission.query.filter(
            AccountProtectedObjectPermission.account_username.\
            in_(self.accounts)).delete(synchronize_session=False)
        Account.query.filter(Account.username.in_(self.accounts)).\
            delete(synchronize_session=False)

        self.accounts = set()

    def delete_scores(self):
        """Delete all scores for all tournaments injected"""

        for tourn in self.tournaments().all():

            if tourn is None:
                return

            tourn.tournament_scores.delete()

            for cat in tourn.score_categories:
                for score in cat.scores:
                    score.game_scores.delete()
                cat.scores.delete()
            tourn.score_categories.delete()
        db.session.commit()

    def delete_tournaments(self):
        """Delete tournaments and their rounds"""

        if not len(self.tournament_ids):
            return

        tourns = self.tournaments()
        permission_ids = [t.protected_object.id for t in tourns.all()]
        creators = Account.query.filter(
            Account.username.in_([t.creator_username for t in tourns.all()]))

        tourns.delete(synchronize_session=False)
        AccountProtectedObjectPermission.query.filter(
            AccountProtectedObjectPermission.account_username.\
            in_([c.username for c in creators.all()])).\
            delete(synchronize_session=False)
        ProtObjPerm.query.\
            filter(ProtObjPerm.protected_object_id.in_(permission_ids)).\
            delete(synchronize_session=False)
        ProtectedObject.query.\
            filter(ProtectedObject.id.in_(permission_ids)).\
            delete(synchronize_session=False)
        creators.delete(synchronize_session=False)

        self.tournament_ids = set()
        self.tournament_names = set()

    def tournaments(self):
        """query the tournaments. Call all to get list"""
        from sqlalchemy.sql import false
        return Tournament.query.filter(Tournament.id.in_(self.tournament_ids)) \
        if len(self.tournament_ids) else Tournament.query.filter(false())
