#!/bin/bash


python manage.py makemigrations 
python manage.py makemigrations protoLib
python manage.py makemigrations protoExt
python manage.py makemigrations prototype
python manage.py migrate 

