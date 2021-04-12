# -*- coding: utf-8 -*-

from .authz import init_authz
from .dashboard import init_dashboard
from .model import init_db
from .team import init_team_api
from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    app.config.from_envvar('BILUOCHUN_CONFIG_PATH')
    # Wrapped with CORS
    CORS(app, supports_credentials = True)

    init_db(app)
    init_authz(app)
    init_dashboard(app)
    init_team_api(app)

    @app.route('/')
    def index():
        return {} # Empty json, implying "it is at least running"

    return app
