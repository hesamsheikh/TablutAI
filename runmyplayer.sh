#!/bin/bash

if [ $# -ne 3 ]; then
  echo "Need all arguments"
  echo "white or black as a first parameter"
  echo "timeout as a second parameter"
  echo "server ip as a third parameter"
  exit 1
fi

python3 Client.py $1 $2 $3
