#!/bin/bash


pip install -r requirements.txt
python manage.py migrate --noinput 
python manage.py collectstatic --noinput 
