from flask_admin.contrib.sqla import ModelView
from flask import request, Response
from werkzeug.exceptions import HTTPException


class AuthModelView(ModelView):
    def is_accessible(self):
        auth = request.authorization or request.environ.get('REMOTE_USER')  # workaround for Apache
        if not auth or (auth.username, auth.password) != ('admin', 'password123'):
            raise HTTPException('', Response(
                "Please log in.", 401,
                {'WWW-Authenticate': 'Basic realm="Login Required"'}
            ))
        return True

class GameView(AuthModelView):
    column_list = ('id', 'player_a', 'player_b', 'score_a', 'score_b', 'timestamp')
    can_create = True


class DoublesView(AuthModelView):
    column_list = ('id', 'player_a_team_a', 'player_b_team_a',
    'player_a_team_b', 'player_b_team_b',  'score_team_a', 'score_team_b')
    can_create = True


class PlayerView(AuthModelView):
    column_list = ('player_id', 'first_name', 'last_name', 'alias')


class RatingsView(AuthModelView):
    column_list = ('alias', 'rating', 'sigma', 'tau', 'pi', 'trueskill')