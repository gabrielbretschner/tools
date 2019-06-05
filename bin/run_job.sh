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
    echo "  -c | --commit            : (required) The commit hash of neural";
    echo "  --config                 : (required) Path to the config file used in neural";
    echo "  -n | --name              : (required) Experiment Name (needs to be unique. Is used as output folder in gs bucket";
    echo "  -e | --env               : The environment file to use. Default ~/.lilt_run_job.env";
    ech "   --region                 : node region (default: us-west1-b)";
    echo "  -h | --help              : This message";
}

function parse_args
{
  # positional args
  args=()

  # named args
  while [[ "$1" != "" ]]; do
      case "$1" in
        -c | --commit )               commit="$2";             shift;;
        --config )                    config="$2";             shift;;
        -e | --env )                  environment="$2";        shift;;
        -n | --name )                 name="$2";               shift;;
        --region )                    REGION="$2";             shift;;
        --)                                                    shift; break;;
        -h | --help )                 usage;                   exit;; # quit and show usage
        * )                           usage;                   exit;; # quit and show usage
      esac
      shift # move to next kv pair
  done

  positional_args="$@"
  # restore positional args
  # set -- "$@"
  # validate required args
  if [[ -z "${commit}" || -z "${config}" || -z "${name}" ]]; then
      echo "Invalid arguments"
      echo "commit: ${commit}"
      echo "config: ${config}"
      echo "name:   ${name}"
      usage
      exit;
  fi

    # set defaults
    if [[ -z "$environment" ]]; then
      environment="$HOME/.lilt_run_job.env";
    fi
    if [[ -z "$REGION" ]]; then
        export REGION="us-west1-b"
    fi

}


function run
{
    parse_args "$@"

    # Export the vars in .env into your shell:
    export $(egrep -v '^#' $environment | xargs)

    package="$checkout_dir/$commit.tar.gz"
    target_package_path=${gs_job_dir%/}/$commit.tar.gz
    job_dir="${gs_job_dir%/}/$name/"
    package_path=$(checkout_code --env=$environment -c $commit --get-path)

    if [[ ! -e $package ]]; then
        checkout_code --env=$environment -c $commit
        pushd .
        cd $package_path/scripts/
        ./lilt-batch-updater-package
        popd
        mv $package_path/scripts/lilt-trainer.tar.gz $package
        gsutil cp $package $target_package_path
    fi

    if [[ -e "$config" ]]; then
        target_config=${job_dir%/}/`basename $config`
        gsutil cp $config $target_config
    else
        echo "$config does not exists"
        exit
    fi
    gcloud ml-engine jobs submit training $name \
            --job-dir $job_dir \
            --runtime-version 1.8 \
            --module-name trainer.neural \
            --staging-bucket  gs://lilt_secondary-cloud-ml \
            --packages $target_package_path\
            --region $REGION\
            --config ${package_path}/scripts/config.yaml \
            -- \
            --trans-out ${job_dir%/}/output.hyp \
            --config $target_config \
            $positional_args
    gcloud ai-platform jobs stream-logs $name
}



run "$@";