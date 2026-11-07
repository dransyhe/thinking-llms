#!/usr/bin/env bash
#SBATCH --job-name=train-saes-qwen3-4b-instruct
#SBATCH --partition=gems
#SBATCH --account=gems
#SBATCH --nodelist=soal-12
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --gres=gpu:4
#SBATCH --mem=400G
#SBATCH --time=48:00:00
#SBATCH --output=/scr/heyu/thinking-llms/logs/slurm/%x-%j.out
#SBATCH --error=/scr/heyu/thinking-llms/logs/slurm/%x-%j.err

# SAE reasoning taxonomy for Qwen/Qwen3-4B-Instruct-2507 at LAYERS (default: the middle layer only;
# train_saes_qwen3_4b_instruct_sweep.sh runs the paper's 6-layer sweep):
#   0. data.clrs.generate                        CLRS-30 textual problems from DATA_CONFIG (DATASET=clrs; default
#                                                data/clrs/config_50per_algo.yaml, 50 problems per algorithm)
#   1. generate-responses/generate_responses.py  DATASET (clrs, or mmlu-pro test split), greedy, vLLM
#   2. train-saes/generate_activations.py        sentence-mean activations at every layer in LAYERS, one pass
#   3. train-saes/train_clustering.py            top-k (k=3) SAEs, one per layer and size in CLUSTERS
#   4. label_eval_saes_qwen3_4b_instruct.sh      local-judge labels for every layer in LAYERS (LABEL=0 skips it),
#                                                with the algorithmic-primitive prompt by default (ALGO=1, labels
#                                                only); ALGO=0 uses the default prompt and also evaluates
#
#   sbatch train_saes_qwen3_4b_instruct.sh
#   sbatch --export=ALL,LAYERS="12 20",CLUSTERS="10 15" train_saes_qwen3_4b_instruct.sh
#   sbatch --export=ALL,DATASET=mmlu-pro,ALGO=0 train_saes_qwen3_4b_instruct.sh
# Every artifact is named by ARTIFACT_ID = <model id>_<dataset tag> (the tag is the data file's stem,
# empty for MMLU-Pro), so CLRS and MMLU-Pro runs never overwrite each other.

set -euo pipefail
ROOT=/scr/heyu/thinking-llms
cd "$ROOT"
mkdir -p logs/slurm
source .venv/bin/activate
export PYTHONPATH="$ROOT" PYTHONUNBUFFERED=1 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export VLLM_CACHE_ROOT=/scr/heyu/.cache/vllm TRITON_CACHE_DIR=/scr/heyu/.cache/triton

MODEL="${MODEL:-Qwen/Qwen3-4B-Instruct-2507}"
MODEL_ID="$(basename "$MODEL" | tr '[:upper:]' '[:lower:]')"
NUM_LAYERS="$(python -c "from transformers import AutoConfig; print(AutoConfig.from_pretrained('$MODEL').num_hidden_layers)")"
LAYERS="${LAYERS:-$(( NUM_LAYERS / 2 ))}"
N_EXAMPLES="${N_EXAMPLES:-100000}"
MAX_TOKENS="${MAX_TOKENS:-10000}"
TP="${TP:-1}"
CLUSTERS="${CLUSTERS:-30}"
LABEL="${LABEL:-1}"
ALGO="${ALGO:-1}"
DATA_CONFIG="${DATA_CONFIG:-data/clrs/config_50per_algo.yaml}"
source "$ROOT/dataset.sh"

RESPONSES="generate-responses/results/vars/responses_${ARTIFACT_ID}.json"

echo "Model:      $MODEL ($NUM_LAYERS layers)"
echo "Layers:     $LAYERS"
echo "Dataset:    $DATASET ${DATA_FILE:-TIGER-Lab/MMLU-Pro test} (artifact id $ARTIFACT_ID)"
echo "Examples:   $N_EXAMPLES (cap; CLRS 50 x 30 = 1,500, MMLU-Pro test 12,032)"
echo "Max tokens: $MAX_TOKENS, vLLM tensor parallel: $TP"
echo "Clusters:   $CLUSTERS"
echo "Labelling:  $( (( LABEL == 0 )) && echo off || { (( ALGO == 1 )) && echo algorithmic-primitive prompt || echo default prompt + evaluation; } )"
nvidia-smi -L

if [[ -n "$DATA_FILE" ]]; then
  echo "=== 0/4 data ($DATA_CONFIG) ==="
  python -m data.clrs.generate --config "$DATA_CONFIG"
fi
[[ -z "$DATA_FILE" || -f "$DATA_FILE" ]] || { echo "missing $DATA_FILE" >&2; exit 1; }

# Responses are regenerated whenever the problems or MAX_TOKENS change; the activation cache in turn
# rebuilds itself whenever the responses file changes (utils.process_saved_responses).
STAMP="data=${DATA_FILE:+$(sha256sum "$DATA_FILE" | cut -d' ' -f1)} max_tokens=$MAX_TOKENS"
echo "=== 1/4 responses ==="
if [[ -f "$RESPONSES" && "$(cat "$RESPONSES.stamp" 2>/dev/null)" == "$STAMP" ]]; then
  echo "up to date: $RESPONSES"
else
  (cd generate-responses && python generate_responses.py --model "$MODEL" --max_tokens "$MAX_TOKENS" \
    --engine vllm --tensor_parallel_size "$TP" "${RESPONSE_FLAGS[@]}")
  echo "$STAMP" > "$RESPONSES.stamp"
fi
[[ -f "$RESPONSES" ]] || { echo "missing $RESPONSES" >&2; exit 1; }

echo "=== 2/4 activations (layers $LAYERS) ==="
(cd train-saes && python generate_activations.py --model "$MODEL" --layers $LAYERS --n_examples "$N_EXAMPLES" \
  --dataset_tag "$DATASET_TAG")
for layer in $LAYERS; do
  activations="generate-responses/results/vars/activations_${ARTIFACT_ID}_${N_EXAMPLES}_${layer}.pkl"
  [[ -f "$activations" ]] || { echo "missing $activations" >&2; exit 1; }
done

for layer in $LAYERS; do
  echo "=== 3/4 SAEs (sae_topk, layer $layer) ==="
  (cd train-saes && python train_clustering.py --model "$MODEL" --layer "$layer" --clusters $CLUSTERS \
    --n_examples "$N_EXAMPLES" --clustering_methods sae_topk --dataset_tag "$DATASET_TAG")
  for n in $CLUSTERS; do
    ckpt="train-saes/results/vars/saes/sae_${ARTIFACT_ID}_layer${layer}_clusters${n}.pt"
    [[ -f "$ckpt" ]] || { echo "missing $ckpt" >&2; exit 1; }
  done
done

echo "SAEs -> train-saes/results/vars/saes/sae_${ARTIFACT_ID}_layer{${LAYERS// /,}}_clusters{${CLUSTERS// /,}}.pt"

if (( LABEL == 1 )); then
  for layer in $LAYERS; do
    echo "=== 4/4 labels (layer $layer) ==="
    MODEL="$MODEL" N_EXAMPLES="$N_EXAMPLES" DATASET="$DATASET" DATA_CONFIG="$DATA_CONFIG" LAYER="$layer" \
      CLUSTERS="$CLUSTERS" ALGO="$ALGO" bash label_eval_saes_qwen3_4b_instruct.sh
  done
fi
echo DONE
