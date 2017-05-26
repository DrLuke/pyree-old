#!/bin/bash

cd /home/drluke/pyree
xset dpms 0 0 0
xset s off -dpms
exec python3 worker.py