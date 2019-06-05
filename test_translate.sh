#!/usr/bin/env bash
#
# ./test_translate.sh neural_config refrence_file target_bpe [git_hash]
#
NEURAL_HOME="$HOME/src/neural"
CHECKOUT_DIR='/tmp/git/'
EXP_DIR=$(pwd)
NEURAL_CONFIG=$1
REFERENCE=$2
TARGET_BPE=$3
git_hash=$4

function config_hash(){
	echo $(sha256sum "$NEURAL_CONFIG" | cut -d' ' -f1)
}
function result_dir(){
	short_config_hash=$(sha256sum "$NEURAL_CONFIG" | cut -d' ' -f1 | awk '{print substr($0,0,10)}')
	short_git_hash=$(echo "$git_hash" | awk '{print substr($0,0,10)}' )
	echo "run.git.${short_git_hash}.config.${short_config_hash}"
}

function run_translate(){
	# run_translate(path, mode, hash, args)
	path=$1
	mode=$2
	git_hash=$3
	args=$4
	log_file="${path}/${mode}.${git_hash}.log"
	hyp_file="${path}/${mode}.${git_hash}.hyp"
	mode_arg=""
	if [[ "$mode" == "greedy" ]]; then
		mode_arg="translate.mode=greedy"
  else
    mode_arg="translate.mode=beam"
	fi
	if [[ ! -e "$hyp_file" ]]; then
		python "$ppath/src/python/neural.py" "--config=$NEURAL_CONFIG" "--mode=translate" $mode_arg "translate.output.0=$hyp_file" $args > "$log_file" 2>&1
		spm_decode --model "$TARGET_BPE" "$hyp_file" | sacrebleu "$REFERENCE" >> "$log_file"
	fi
	echo "$log_file"
}

function run_experiment(){
	mode=$1
	batch_size=$2
	beam_size=$3
	if [[ ! ("$mode" != "greedy" || ("$batch_size" == 1 && "$beam_size" == 1)) ]]; then
		echo "greedy mode requires batch 1 and beam 1"
		exit 1
	fi
	echo "translate $mode.$batch_size.$beam_size"
	log_file=$(run_translate "$result_path" "$mode" "$git_hash" "translate.batch-size=${batch_size} translate.beam-size=${beam_size}")
	echo "done"
	ws=$(grep "words/sec" "$log_file" | cut -d' ' -f11,12)
	bleu=$(grep BLEU "$log_file" | cut -d= -f2 |cut -d' ' -f2)
	res="${mode}.beam.${beam_size}.batch.${batch_size}: ${ws} ${bleu}"
	echo "$res"
	result_string="${result_string}\n$res"
}

function activate_virtualenv(){
	if [[ "$OSTYPE" == "darwin"* ]]; then
	  source "/usr/local/miniconda3/etc/profile.d/conda.sh" || exit
	  conda activate neural || exit
	else
	  source "$HOME/.virtualenvs/neural/bin/activate"
    fi
}

function checkout_neural(){
	if [[ "$git_hash" == "" ]]; then
		cd "$NEURAL_HOME" || exit
		git_hash=$(git rev-parse HEAD)
	fi
	echo "checkout $git_hash"
	checkout_code --repository "$NEURAL_HOME" --checkout-dir "$CHECKOUT_DIR" --use-prefix --commit-hash "$git_hash" &> /dev/null
	ppath=$(checkout_code --repository "$NEURAL_HOME" --checkout-dir "$CHECKOUT_DIR" --use-prefix --commit-hash "$git_hash" --get-path 2> /dev/null)

	if [[ "$ppath" == "" ]]; then
		echo "checkout path empty. something went wrong"
		exit 1
	fi
}

activate_virtualenv
checkout_neural

cd $EXP_DIR || exit
echo "done"
export PYTHONPATH="$ppath:$PYTHONPATH"

result_path=$(result_dir)
mkdir -p "$result_path"
echo "output to $result_path"
cp "$NEURAL_CONFIG" "$result_path/"

title="command used: $0 $*\ngit-hash: $git_hash \nconfig hash: $(config_hash)"
result_string=""

run_experiment "greedy" "1" "1"
run_experiment "beam" "1" "1"
run_experiment "beam" "1" "100"
run_experiment "beam" "2" "1"
run_experiment "beam" "2" "100"
echo
echo
echo -e "$title\n$(echo -e "$result_string" | column -t -s' ')" | tee -a "${result_path}/results.log"
