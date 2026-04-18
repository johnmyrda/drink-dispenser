#!/usr/bin/env bash

program_name=basic_bar
pgrep -a $program_name
running=$?


if [ "$running" -eq "0" ]; then
  echo "Program $program_name is already running. Exiting.."
  exit 0;
else
  script_directory=$(dirname "$0")
  cd "$script_directory" || echo "Failed to cd to $script_directory" || exit 1
  echo "Started $program_name at $(date)" >> startup.log
  nohup uv run basic_bar >/dev/null 2>&1 &
fi;