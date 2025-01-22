#!/usr/bin/env bash

pip install isort black yapf

isort --profile black src --skip src/smart_camera_interface_schema
black --line-length 80 src --exclude src/smart_camera_interface_schema
yapf --style='{based_on_style: google}' --print-modified -ir src --exclude src/smart_camera_interface_schema

pylint --rcfile ./pylintrc --indent-string '    ' src --ignore smart_camera_interface_schema
