#!/bin/bash

VIRTUALENV=.virtualenv

python3 -m venv $VIRTUALENV

source $VIRTUALENV/bin/activate

pip install --upgrade pip

pip install -r ./requirements.txt
