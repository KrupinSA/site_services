from flask_restful import Resource, url_for, reqparse
from flask import current_app, g, send_file, jsonify
import threading
from threading import Thread
from .tasks import threaded_task, get_image_work_path, sites_id
import random


parser = reqparse.RequestParser()
parser.add_argument('url')

def bad_request(e):
    response = jsonify({'status': 'bad request'})
    response.status_code = 400
    return response

def page_not_found(e):
    response = jsonify({'status': 'source not found'})
    response.status_code = 404
    return response

def internal_server_error(e):
    response = jsonify({'status': 'Internal server error'})
    response.status_code = 500
    return response

class GetSite(Resource):

    def get(self, id):
        '''
        Get create status site from id and url to download this site. 
        GET /api/v1.0/<string:id>
        '''
        if id in (thread.name for thread in threading.enumerate()):
            return {'status': 'making',
                    'url': None}, 404
        if id in sites_id:            
            return {'status': 'created',
                    'id': id,
                    'url': url_for('bp.downloadsite', id=id)}, 200
        
        return {'status': 'Site not found'}, 404



class MakeSite(Resource):

    def post(self):
        '''
        Add new url site to making arhive
        POST /api/v1.0/  .etc text=https://wwww.example.com
        '''
        args = parser.parse_args()
        if not args['url']: 
            return {'status': 'Empty url'}, 400
        thread = Thread(target=threaded_task, args=(args['url'],
                                                current_app.config['SITE_DIR'],
                                                current_app.config['PATH_LEVEL'],
                                               ))
        thread.daemon = True
        thread.start()
        thread.setName(str(random.randint(100,999)))
        sites_id.add(thread.name)
        return {'status': 'making',
                'id': thread.name,
                'url': url_for('bp.downloadsite', id=thread.name)}, 201


class DownloadSite(Resource):

    def get(self, id):
        '''
        Download file with id
        GET /api/v1.0/download/<string:id>
        '''
        try:
            return send_file(get_image_work_path(id), 
                            mimetype="application/zip",
                            attachment_filename=id+".zip"
                            )
        except FileNotFoundError:
            return {'status': 'File not found'}, 404

