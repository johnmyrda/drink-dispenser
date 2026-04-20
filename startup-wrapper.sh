#!/usr/bin/env bash

program_name="uv run basic_bar"
pgrep -f -a "$program_name"
running=$?


if [ "$running" -eq "0" ]; then
  echo "Program '$program_name' is already running. Exiting.."
  exit 0;
else
  script_directory=$(dirname "$0")
  cd "$script_directory" || echo "Failed to cd to $script_directory" || exit 1
  nohup uv run basic_bar >/dev/null 2>&1 &
  program_pid=$(pgrep -f "$program_name")
  echo "Started '$program_name' [$program_pid] $(date)"
fi;