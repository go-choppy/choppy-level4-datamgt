#!/usr/bin/env python
# -*- encoding:utf-8 -*-
import os, sys

from level4_data_mgt import app
from level4_data_mgt.urls import level4_data_mgt_bp
app.register_blueprint(level4_data_mgt_bp)

if __name__ == '__main__':
    app.run(debug=True, port=app.config.get('HTTPPORT'))
