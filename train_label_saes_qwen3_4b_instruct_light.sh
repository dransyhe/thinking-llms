#!/usr/bin/env bash
#SBATCH --job-name=train-label-saes-qwen3-4b-instruct-light
#SBATCH --partition=gems
#SBATCH --account=gems
#SBATCH --nodelist=soal-12
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --gres=gpu:4
#SBATCH --mem=200G
#SBATCH --time=24:00:00
#SBATCH --output=/scr/heyu/thinking-llms/logs/slurm/%x-%j.out
#SBATCH --error=/scr/heyu/thinking-llms/logs/slurm/%x-%j.err

# Light CLRS setting for Qwen/Qwen3-4B-Instruct-2507: 50 problems per algorithm (data/clrs/config_50per_algo.yaml,
# artifact id qwen3-4b-instruct-2507_clrs_50per_algo), layer 18 only, and one cluster size at a time:
# train_saes_qwen3_4b_instruct.sh trains size n, then label_eval_saes_qwen3_4b_instruct.sh labels it with the
# algorithmic-primitive prompt (ALGO=1, labels only, into the *_algo.json results file) before the next size.
# Responses and activations are built by the first size and reused by the rest. Each labelling round also writes
# its own log, logs/slurm/<job name>-<job id>-label-clusters<n>.log.
#
#   sbatch train_label_saes_qwen3_4b_instruct_light.sh
#   sbatch --export=ALL,ALGO=0 train_label_saes_qwen3_4b_instruct_light.sh   (default cognitive-function labels)

set -euo pipefail
cd /scr/heyu/thinking-llms
export DATASET=clrs DATA_CONFIG="${DATA_CONFIG:-data/clrs/config_50per_algo.yaml}"
export MAX_TOKENS="${MAX_TOKENS:-16384}" ALGO="${ALGO:-1}" EVALUATE="${EVALUATE:-0}"
LAYER="${LAYER:-18}"
ARTIFACT_ID="qwen3-4b-instruct-2507_$(basename "$(python3 -c 'import sys, yaml; print(yaml.safe_load(open(sys.argv[1]))["output_jsonl"])' "$DATA_CONFIG")" .jsonl)"
ACTIVATIONS="generate-responses/results/vars/activations_${ARTIFACT_ID}_${N_EXAMPLES:-100000}_${LAYER}.pkl"
for n in ${SIZES:-5 20 50}; do
  # A resubmission skips sizes whose SAE was already trained on the current activations
  ckpt="train-saes/results/vars/saes/sae_${ARTIFACT_ID}_layer${LAYER}_clusters${n}.pt"
  if [[ -f "$ckpt" && "$ckpt" -nt "$ACTIVATIONS" ]]; then
    echo "##### cluster size $n: train (up to date: $ckpt) #####"
  else
    echo "##### cluster size $n: train #####"
    LAYERS="$LAYER" CLUSTERS="$n" LABEL=0 bash train_saes_qwen3_4b_instruct.sh
  fi
  label_log="logs/slurm/${SLURM_JOB_NAME:-train-label-light}-${SLURM_JOB_ID:-local}-label-clusters$n.log"
  echo "##### cluster size $n: label (log: $label_log) #####"
  LAYER="$LAYER" CLUSTERS="$n" bash label_eval_saes_qwen3_4b_instruct.sh 2>&1 | tee "$label_log"
done
