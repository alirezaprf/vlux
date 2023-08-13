#!/bin/bash

set -e

if [ -d "vlux" ]; then
    cd vlux
    git pull
else
    git clone https://github.com/alirezaprf/vlux
    cd vlux
fi
pip install -r requirements.txt
exec $@
