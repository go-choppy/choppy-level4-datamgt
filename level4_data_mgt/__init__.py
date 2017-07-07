from flask import Flask, Blueprint
from flask_httpauth import HTTPBasicAuth
from flask_mongoengine import MongoEngine
from logging.handlers import RotatingFileHandler
from logging import StreamHandler
import logging, json
import os, sys

db = MongoEngine()

BASEDIR = os.path.dirname(__file__)
JSON_TEMPLATES_DIR = BASEDIR + '/json_templates'

def create_app(config_name):
    # initialization
    app = Flask(__name__)
    # 抑制Jinja2产生空行/空格
    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True
    try:
        working_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
        f = open(os.path.join(working_dir, config_name), "r")
        app.config.update(json.load(f))
    except IOError as err:
        print("No such file: %s" % os.path.abspath(config_name))
        sys.exit(1)
    finally:
        if 'f' in locals():
            f.close()

    db.init_app(app)
    # Set log file
    LOGLEVEL = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR
    }
    log_file = app.config.get("LOGFILE")
    level = app.config.get("LOGLEVEL")
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler = RotatingFileHandler(log_file)
    handler.setLevel( LOGLEVEL.get(level) )
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)

    # if app.config.get("STREAM_HANDLER_STATUS"):
    #     stream_handler = StreamHandler(sys.stdout)
    #     stream_handler.setLevel( LOGLEVEL.get(level) )
    #     stream_handler.setFormatter(formatter)
    #     app.logger.addHandler(stream_handler)

    return app

app = create_app(os.getenv('config') or 'level4_data_mgt/config.json')
DBDataDir = app.config.get('DBDataDir')