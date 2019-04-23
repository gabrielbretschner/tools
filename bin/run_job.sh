#!/usr/bin/env bash

#
# run a job using ml-toolkit
#
# 1. generate package given a commit hash
# 2. upload package to predefined bucket
# 3. upload config to predefined bucket
# 4. run job

#abort on error
set -e

function usage
{
    echo "usage: run_job.sh -c COMMIT"
    echo "   ";
    echo "  -c | --commit            : The commit hash of neural";
    echo "  -e | --env               : The environment file to use. Default ~/.lilt_run_job.env";
    echo "  -h | --help              : This message";
}

function parse_args
{
  # positional args
  args=()

  # named args
  while [ "$1" != "" ]; do
      case "$1" in
          -c | --commit )               commit="$2";             shift;;
          -e | --env )                  environment="$2";        shift;;
          -h | --help )                 usage;                   exit;; # quit and show usage
          * )                           args+=("$1")             # if no match, add it to the positional args
      esac
      shift # move to next kv pair
  done

  # restore positional args
  set -- "${args[@]}"

  # set positionals to vars
  positional_1="${args[0]}"
  positional_2="${args[1]}"

  # validate required args
  if [[ -z "${commit}" ]]; then
      echo "Invalid arguments"
      usage
      exit;
  fi

  # set defaults
  if [[ -z "$environment" ]]; then
      environment="$HOME/.lilt_run_job.env";
  fi
}


function run
{
  parse_args "$@"

  echo "you passed in...\n"
  echo "positional arg 1: $positional_1"
  echo "positional arg 2: $positional_2"

  echo "named arg: commit: $commit"
  echo "named arg: environment: $environment"
}



run "$@";