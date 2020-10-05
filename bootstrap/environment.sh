#!/bin/bash

VENV_DIR="$HOME/Development/test-app/"

function activate_venv {
    source "$VENV_DIR/venv/bin/activate"
    pip list
}

if [ -d "$VENV_DIR/venv" ]; then
  ### Take action if $VENV_DIR exists ###
  echo "Virtual environment exists in ${VENV_DIR}..."
  activate_venv
else
  ###  Control will jump here if $VENV_DIR does NOT exists ###
  echo "Error: ${VENV_DIR} not found. Creating new venv"
  virtualenv "$VENV_DIR/venv"
  activate_venv
fi

# http://matt.might.net/articles/bash-by-example/
