#!/bin/bash
[[ -z "$1" ]] && exit 1
cd $(dirname "$0")/..
rsync -avuzC pycmdbot "$1"
