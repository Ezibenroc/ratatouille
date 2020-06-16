#!/usr/bin/env sh

# This little script launches ratatouille to collect all data
# while executing a script
# The first argument is the interval collect time for ratatouille
# The second argument is the output file of ratatouille
# The third argument is the command script to execute

if [ $# -ne 3 ] ; then
    echo "Usage: $0 <timestep> <output_file> <command>"
    exit 1
fi

timestep=$1
output_file=$2
command=$3

python -m ratatouille collect -t ${timestep} all ${output_file} &
rata_pid=$!
sleep ${timestep}

eval ${command}

sleep ${timestep}
kill -2 ${rata_pid}
