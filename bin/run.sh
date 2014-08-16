#!/bin/bash

cd "$(dirname "$0")"
cd ..

if [ -z "$1" ]; then
  sleep $((RANDOM % 5000))
fi
source $(which virtualenvwrapper.sh)
workon adopte
pkill -f "python adopte/adopte.py"
sleep 5
python adopte/adopte.py >> log.txt 2>&1 &
deactivate
if [ ! -z "$1" ]; then
  tail -f log.txt
fi
