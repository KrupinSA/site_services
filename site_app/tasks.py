from os import path
from flask import current_app
from .parsing_html import main

sites_id = set()

def threaded_task(url, root_dir, path_level=3):
    main(url, root_dir, path_level)

def get_image_work_path(name:str)->str:
    img_dir = current_app.config['SITE_DIR']
    return path.join(img_dir, name) + ".zip"
