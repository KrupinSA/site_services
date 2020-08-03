import os
from flask import Flask, Blueprint,jsonify
from flask_restful import Api


def create_app(test_config=None):

    app = Flask(__name__, instance_relative_config=True )

    try:
        os.makedirs(os.path.join(app.instance_path, 'sites'))

    except OSError:
        pass

    app.config.from_mapping(
        SITE_DIR = os.path.join(app.instance_path, 'sites'),
        PATH_LEVEL = 3,
    )
    
    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    bp_views = Blueprint('bp', __name__, url_prefix='/api/v1.0')
    
    from .views import  GetSite, MakeSite, DownloadSite, bad_request, page_not_found, internal_server_error

    api = Api(bp_views)

    api.add_resource(DownloadSite, '/download/<string:id>')
    api.add_resource(GetSite, '/<string:id>')
    api.add_resource(MakeSite, '/')

    
    app.register_blueprint(bp_views)
    app.register_error_handler(400, bad_request)
    app.register_error_handler(404, page_not_found)
    app.register_error_handler(500, internal_server_error)

    return app