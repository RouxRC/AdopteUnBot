#!/bin/bash

sudo service mongodb restart || (echo "Please install MongoDB beforehand" && exit 1)

sudo apt-get install python-pip
sudo pip install virtualenv
sudo pip install virtualenvwrapper

source $(which virtualenvwrapper.sh)
mkvirtualenv --no-site-packages adopte
workon adopte
pip install -r requirements.txt
add2virtualenv .
deactivate

if ! test -f config.json; then
    cp config.json{.example,}
    echo "Configure your login and password in config.json"
fi
echo "Add to your crontab the following line:"
echo "0 9 * * * bash "$(pwd)"/run.sh"
