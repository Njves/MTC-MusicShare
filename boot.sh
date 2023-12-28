#!/bin/sh
flask db init
flask db migrate
flask db upgrade
exec gunicorn --worker-class eventlet -w 1 -b :5000 main:app