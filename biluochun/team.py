'''
Defines /api/team endpoints series.
'''

from datetime import datetime
import secrets

from flask import Blueprint, redirect, request, url_for
from flask.json import jsonify
from flask_login import current_user, login_required

from .form import Avatar, TeamInfo
from .model import Image, Team, TeamCreation, db
from .qq import qq_verify_required
from .util import cleanse_profile_pic, find_team_by_name, team_summary, user_summary
from .webhook import trigger_webhook


def init_team_api(app):
    '''
    Initialize the app with /api/team endpoints series.
    '''
    bp = Blueprint('team', __name__, url_prefix = '/api/team')

    @bp.after_request
    def cdn_please_stop(r):
        r.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, public, max-age=0'
        r.headers['Pragma'] = 'no-cache'
        r.headers['Expires'] = '0'
        return r

    @bp.route('/', methods = [ 'GET' ])
    def list_all_teams():
        # SELECT DISTINCT team.* FROM team
        #   JOIN user ON team.id = user.team_id
        #   ORDER BY team.id;
        detailed = request.args.get('detailed', False, type = bool)
        teams = Team.query.distinct().join(Team.members).order_by(Team.id)
        if 'page' in request.args:
            page_index = request.args.get('page', 1, type = int)
            page_size = request.args.get('size', 10, type = int)
            page = teams.paginate(page_index, page_size, error_out = False)
            return {
                'current': page.page,
                'first': 1,
                'last': page.pages,
                'prev': page.prev_num,
                'next': page.next_num,
                'teams': [team_summary(team, detailed=detailed) for team in page.items]
            }
        return jsonify([team_summary(team, detailed=detailed) for team in teams])

    @bp.route('/', methods = [ 'POST' ])
    @login_required
    @qq_verify_required
    def create_team():
        if current_user.team_id is None:
            new_team = Team(id = None, name = f"{current_user.name}'s team", \
                mod_name = f"{current_user.name}'s mod", invite = secrets.token_hex(8), \
                profile_pic_id = 2)
            current_user.team = new_team
            form = TeamInfo()
            if form.validate_on_submit():
                if form.name.data is not None:
                    new_team.name = form.name.data
                if form.mod_name.data is not None:
                    new_team.mod_name = form.mod_name.data
                if form.desc.data is not None:
                    new_team.description = form.desc.data
                if form.repo.data is not None:
                    new_team.repo = form.repo.data
            else:
                return {
                    'error': 'Form contains error. Check "details" field for more information.',
                    'details': form.errors
                }, 400
            # Commit the changes
            db.session.add(new_team)
            db.session.commit()
            creation_time = TeamCreation(id = new_team.id, creation = datetime.utcnow())
            db.session.add(creation_time)
            db.session.commit()
            trigger_webhook(new_team, "create")
            return {}
        else:
            return { 'error': 'You have already been in a team!' }, 400

    # Used for determining if a team name if available
    @bp.route('/name/<team_name>', methods = [ 'GET' ])
    def show_team_by_name(team_name):
        team = find_team_by_name(team_name)
        return { 'resutl': team is None }

    @bp.route('/<int:team_id>', methods = [ 'GET' ])
    def show_team(team_id):
        team = Team.query.get(team_id)
        return ({ 'error': 'No such team' }, 404) if team is None else team_summary(team, detailed = True)

    @bp.route('/<int:team_id>', methods = [ 'POST' ])
    @login_required
    @qq_verify_required
    def update_team(team_id):
        team = Team.query.get(team_id)
        if team is None:
            return { 'error': 'No such team' }, 404
        if current_user.team_id != team.id:
            return { 'error': f"You are not in team '{team.name}'!" }, 400
        form = TeamInfo(target_team = team)
        if form.validate_on_submit():
            if form.name.data is not None:
                team.name = form.name.data
            if form.mod_name.data is not None:
                team.mod_name = form.mod_name.data
            if form.desc.data is not None:
                team.description = form.desc.data
            if form.repo.data is not None:
                team.repo = form.repo.data
            # Commit the changes
            db.session.commit()
            trigger_webhook(team, "update")
            return {}
        else:
            return {
                'error': 'Form contains error. Check "details" field for more information.',
                'details': form.errors
            }, 400

    @bp.route('/<int:team_id>/members', methods = [ 'GET' ])
    def get_team_members(team_id):
        team = Team.query.get(team_id)
        return ({ 'error': 'No such team' }, 404) if team is None \
            else jsonify([ user_summary(member) for member in team.members ])

    @bp.route('/<int:team_id>/avatar', methods = [ 'GET' ])
    @bp.route('/<int:team_id>/icon', methods = [ 'GET' ])
    @bp.route('/<int:team_id>/profile_pic', methods = [ 'GET' ])
    def get_team_icon(team_id):
        team = Team.query.get(team_id)
        if team is None:
            return { 'error': 'No such team' }, 404
        return redirect(url_for('image.get_image', img_id = team.profile_pic_id))

    @bp.route('/<int:team_id>/avatar', methods = [ 'POST' ])
    @bp.route('/<int:team_id>/icon', methods = [ 'POST' ])
    @bp.route('/<int:team_id>/profile_pic', methods = [ 'POST' ])
    @login_required
    @qq_verify_required
    def update_team_icon(team_id):
        team = Team.query.get(team_id)
        if team is None:
            return { 'error': 'No such team' }, 404
        if current_user.team_id != team.id:
            return { 'error': f"You are not in team '{team.name}'!" }, 400
        form = Avatar()
        if form.validate_on_submit():
            team.profile_pic = Image(id = None, data = cleanse_profile_pic(form.avatar.data))
            db.session.commit()
            return {}
        else:
            return {
                'error': 'Form contains error. Check "details" field for more information.',
                'details': form.errors
            }, 400

    app.register_blueprint(bp)
