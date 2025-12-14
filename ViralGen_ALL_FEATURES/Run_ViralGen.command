#!/bin/bash
cd "$(dirname "$0")"
python3 app.py
open http://127.0.0.1:5000
