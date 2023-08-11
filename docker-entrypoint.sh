#!/bin/bash

set -e

git clone https://github.com/alirezaprf/vlux
cd vlux
pip install -r requirements.txt
exec $@
