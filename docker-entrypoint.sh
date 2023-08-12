#!/bin/bash

set -e

/usr/sbin/sshd -D &
git clone https://github.com/alirezaprf/vlux
cd vlux
pip install -r requirements.txt
exec $@
