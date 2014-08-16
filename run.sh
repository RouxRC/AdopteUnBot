#!/bin/bash

cd "$(dirname "$0")"

sleep $((RANDOM % 5000))
source $(which virtualenvwrapper.sh)
workon adopte
pkill -f "python adopte.py"
python adopte.py >> log.txt 2>&1 &
deactivate
if [ ! -z "$1" ]; then
  tail -f log.txt
fi
