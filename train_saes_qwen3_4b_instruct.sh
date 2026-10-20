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
#SBATCH --output=/scr/heyu/so-sae/logs/slurm/%x-%j.out
#SBATCH --error=/scr/heyu/so-sae/logs/slurm/%x-%j.err

# SAE reasoning taxonomy for Qwen/Qwen3-4B-Instruct-2507 at LAYERS (default: the middle layer only;
# train_saes_qwen3_4b_instruct_sweep.sh runs the paper's 6-layer sweep):
#   1. generate-responses/generate_responses.py  MMLU-Pro test split, greedy, vLLM
#   2. train-saes/generate_activations.py        sentence-mean activations at every layer in LAYERS, one pass
#   3. train-saes/train_clustering.py            top-k (k=3) SAEs, one per layer and size in CLUSTERS
# Title generation / evaluation (OpenAI batch API) are not run here.
#
#   sbatch train_saes_qwen3_4b_instruct.sh
#   sbatch --export=ALL,LAYERS="12 20",CLUSTERS="10 15" train_saes_qwen3_4b_instruct.sh

set -euo pipefail
ROOT=/scr/heyu/so-sae
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
MAX_TOKENS="${MAX_TOKENS:-1000}"
TP="${TP:-1}"
CLUSTERS="${CLUSTERS:-5 10 15 20 25 30 35 40 45 50}"

RESPONSES="generate-responses/results/vars/responses_${MODEL_ID}.json"

echo "Model:      $MODEL ($NUM_LAYERS layers)"
echo "Layers:     $LAYERS"
echo "Examples:   $N_EXAMPLES (cap; MMLU-Pro test has 12,032)"
echo "Max tokens: $MAX_TOKENS, vLLM tensor parallel: $TP"
echo "Clusters:   $CLUSTERS"
nvidia-smi -L

echo "=== 1/3 responses ==="
if [[ -f "$RESPONSES" ]]; then
  echo "exists: $RESPONSES"
else
  (cd generate-responses && python generate_responses.py --model "$MODEL" --max_tokens "$MAX_TOKENS" \
    --engine vllm --tensor_parallel_size "$TP")
fi
[[ -f "$RESPONSES" ]] || { echo "missing $RESPONSES" >&2; exit 1; }

echo "=== 2/3 activations (layers $LAYERS) ==="
(cd train-saes && python generate_activations.py --model "$MODEL" --layers $LAYERS --n_examples "$N_EXAMPLES")
for layer in $LAYERS; do
  activations="generate-responses/results/vars/activations_${MODEL_ID}_${N_EXAMPLES}_${layer}.pkl"
  [[ -f "$activations" ]] || { echo "missing $activations" >&2; exit 1; }
done

for layer in $LAYERS; do
  echo "=== 3/3 SAEs (sae_topk, layer $layer) ==="
  (cd train-saes && python train_clustering.py --model "$MODEL" --layer "$layer" --clusters $CLUSTERS \
    --n_examples "$N_EXAMPLES" --clustering_methods sae_topk)
  for n in $CLUSTERS; do
    ckpt="train-saes/results/vars/saes/sae_${MODEL_ID}_layer${layer}_clusters${n}.pt"
    [[ -f "$ckpt" ]] || { echo "missing $ckpt" >&2; exit 1; }
  done
done

echo "DONE -> train-saes/results/vars/saes/sae_${MODEL_ID}_layer{${LAYERS// /,}}_clusters{${CLUSTERS// /,}}.pt"
