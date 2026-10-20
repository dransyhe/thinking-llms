#!/usr/bin/env bash
#SBATCH --job-name=label-eval-saes-qwen3-4b-instruct
#SBATCH --partition=gems
#SBATCH --account=gems
#SBATCH --nodelist=soal-12
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --gres=gpu:2
#SBATCH --mem=200G
#SBATCH --time=48:00:00
#SBATCH --output=/scr/heyu/so-sae/logs/slurm/%x-%j.out
#SBATCH --error=/scr/heyu/so-sae/logs/slurm/%x-%j.err

# Labels and evaluates the trained Qwen3-4B-Instruct SAEs with a locally served judge instead of
# the OpenAI API (o4-mini for titles, gpt-4.1-mini for evaluation in the paper):
#   GPU 0: vllm serve JUDGE (OpenAI-compatible, reasoning split off by the deepseek_r1 parser)
#   GPU 1: train-saes/generate_titles_trained_clustering.py --command direct   (titles)
#          train-saes/evaluate_trained_clustering.py --command direct           (accuracy,
#          completeness, semantic + centroid orthogonality)
# Both scripts reach the server through LOCAL_LLM_BASE_URL (utils.utils.chat_batch).
# Requires the SAEs and activation cache from train_saes_qwen3_4b_instruct.sh.
#
# ALGO=1 labels with the algorithmic-operation prompt (generate_titles --algo) into a separate
# *_algo.json file and stops after labelling: evaluate_trained_clustering.py only reads the default
# labels file, so EVALUATE=1 is rejected with ALGO=1. EVALUATE=0 skips evaluation in either mode.
#
#   sbatch label_eval_saes_qwen3_4b_instruct.sh
#   sbatch --export=ALL,LAYER=25,CLUSTERS="10 15" label_eval_saes_qwen3_4b_instruct.sh
#   sbatch --export=ALL,ALGO=1,CLUSTERS="5 10 20 50" label_eval_saes_qwen3_4b_instruct.sh

set -euo pipefail
ROOT=/scr/heyu/so-sae
cd "$ROOT"
mkdir -p logs/slurm
source .venv/bin/activate
export PYTHONPATH="$ROOT" PYTHONUNBUFFERED=1 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export VLLM_CACHE_ROOT=/scr/heyu/.cache/vllm TRITON_CACHE_DIR=/scr/heyu/.cache/triton

MODEL="${MODEL:-Qwen/Qwen3-4B-Instruct-2507}"
MODEL_ID="$(basename "$MODEL" | tr '[:upper:]' '[:lower:]')"
JUDGE="${JUDGE:-Qwen/Qwen3-30B-A3B-Thinking-2507}"
JUDGE_CACHE="${JUDGE_CACHE:-/scr/heyu/.cache/huggingface/hub}"
LAYER="${LAYER:-18}"
N_EXAMPLES="${N_EXAMPLES:-100000}"
REPETITIONS="${REPETITIONS:-3}"
CLUSTERS="${CLUSTERS:-5 10 15 20 25 30 35 40 45 50}"
PORT="${PORT:-$(( 20000 + ${SLURM_JOB_ID:-$$} % 10000 ))}"
ALGO="${ALGO:-0}"
EVALUATE="${EVALUATE:-$(( ALGO == 1 ? 0 : 1 ))}"
(( ALGO == 1 && EVALUATE == 1 )) && { echo "EVALUATE=1 is not supported with ALGO=1" >&2; exit 1; }
RESULTS_SUFFIX=""
(( ALGO == 1 )) && RESULTS_SUFFIX=_algo
RESULTS="train-saes/results/vars/sae_topk_results_${MODEL_ID}_layer${LAYER}${RESULTS_SUFFIX}.json"

IFS=, read -r -a GPUS <<< "${CUDA_VISIBLE_DEVICES:?no GPUs allocated}"
(( ${#GPUS[@]} >= 2 )) || { echo "need 2 GPUs, got ${CUDA_VISIBLE_DEVICES}" >&2; exit 1; }

for n in $CLUSTERS; do
  ckpt="train-saes/results/vars/saes/sae_${MODEL_ID}_layer${LAYER}_clusters${n}.pt"
  [[ -f "$ckpt" ]] || { echo "missing $ckpt (run train_saes_qwen3_4b_instruct.sh first)" >&2; exit 1; }
done

echo "SAEs:     $MODEL layer $LAYER, clusters $CLUSTERS"
echo "Judge:    $JUDGE on GPU ${GPUS[0]}, port $PORT; clients on GPU ${GPUS[1]}"
echo "Reps:     $REPETITIONS"
echo "Prompt:   $( (( ALGO == 1 )) && echo algorithmic-operation || echo default ); evaluate: $EVALUATE"
echo "Results:  $RESULTS"

VLLM_LOG="logs/slurm/${SLURM_JOB_NAME:-label-eval}-${SLURM_JOB_ID:-local}.vllm.log"
HF_HUB_CACHE="$JUDGE_CACHE" CUDA_VISIBLE_DEVICES="${GPUS[0]}" vllm serve "$JUDGE" \
  --port "$PORT" --max-model-len 40960 --reasoning-parser deepseek_r1 \
  --gpu-memory-utilization 0.9 --max-num-seqs 256 > "$VLLM_LOG" 2>&1 &
VLLM_PID=$!
trap 'kill $VLLM_PID 2>/dev/null; wait $VLLM_PID 2>/dev/null' EXIT

echo "=== waiting for vLLM (log: $VLLM_LOG) ==="
for _ in $(seq 360); do
  curl -sf "http://localhost:$PORT/health" > /dev/null && break
  kill -0 $VLLM_PID 2>/dev/null || { echo "vLLM exited during startup" >&2; tail -50 "$VLLM_LOG" >&2; exit 1; }
  sleep 5
done
curl -sf "http://localhost:$PORT/health" > /dev/null || { echo "vLLM not healthy after 30 min" >&2; exit 1; }

export LOCAL_LLM_BASE_URL="http://localhost:$PORT/v1" CUDA_VISIBLE_DEVICES="${GPUS[1]}"

echo "=== smoke test ==="
python - "$JUDGE" <<'EOF'
import sys
from utils.clustering import run_chat_batch_with_event_loop_handling
[reply] = run_chat_batch_with_event_loop_handling(["Reply in this exact format:\nTitle: <one word>\nDescription: <one sentence>"], sys.argv[1])
print(reply)
assert "Title:" in reply, f"judge reply has no 'Title:' line: {reply!r}"
EOF

COMMON=(--model "$MODEL" --layer "$LAYER" --clusters $CLUSTERS --n_examples "$N_EXAMPLES"
        --clustering_methods sae_topk --repetitions "$REPETITIONS" --command direct --evaluator_model "$JUDGE")
TITLE_FLAGS=()
(( ALGO == 1 )) && TITLE_FLAGS=(--algo)

missing_labels() {
  python - "$RESULTS" "$REPETITIONS" "$MODEL_ID" "$LAYER" $CLUSTERS <<'EOF'
import json, sys, numpy as np, torch
path, reps, model_id, layer, sizes = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4], sys.argv[5:]
by_size = json.load(open(path))["results_by_cluster_size"]
missing = 0
for n in sizes:
    ckpt = torch.load(f"train-saes/results/vars/saes/sae_{model_id}_layer{layer}_clusters{n}.pt", weights_only=False)
    nonempty = {int(i) for i in np.unique(ckpt["cluster_labels"])}
    for run in (by_size.get(n, {}).get("all_results", []) + [{}] * reps)[:reps]:
        labelled = {int(c[0]) for c in run.get("categories", []) if c[1] != "Unnamed Cluster" and c[2] != "No description available"}
        missing += len(nonempty - labelled)
print(missing)
EOF
}

# The titles script only regenerates missing/placeholder labels, so re-running it retries the
# requests the judge left unfinished (no content after its reasoning). Clusters no sentence is
# assigned to are skipped by the titles script, so they are not counted as missing.
for pass in 1 2 3; do
  echo "=== 1/2 titles (pass $pass) ==="
  (cd train-saes && python generate_titles_trained_clustering.py "${COMMON[@]}" "${TITLE_FLAGS[@]}")
  missing="$(missing_labels)"
  echo "labels still missing: $missing"
  (( missing == 0 )) && break
done
(( missing == 0 )) || { echo "$missing labels still missing after 3 passes" >&2; exit 1; }

if (( EVALUATE == 0 )); then
  echo "DONE (labels only) -> $RESULTS"
  exit 0
fi

echo "=== 2/2 evaluation ==="
(cd train-saes && python evaluate_trained_clustering.py "${COMMON[@]}" --accuracy_target_cluster_percentage 0.2)

python - "$RESULTS" "$REPETITIONS" $CLUSTERS <<'EOF'
import json, sys
path, reps, sizes = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
by_size = json.load(open(path))["results_by_cluster_size"]
problems = []
print(f"{'clusters':>8} {'final':>7} {'unnamed titles':>15}")
for n in sizes:
    entry = by_size.get(n, {})
    runs = entry.get("all_results", [])
    unnamed = sum(c[1] == "Unnamed Cluster" for r in runs for c in r.get("categories", []))
    print(f"{n:>8} {entry.get('avg_final_score', float('nan')):7.4f} {unnamed:>15}")
    if "avg_final_score" not in entry or not entry.get("statistics"):
        problems.append(f"{n}: no evaluation scores")
if problems:
    sys.exit("incomplete results in " + path + ":\n  " + "\n  ".join(problems))
EOF
echo "DONE -> $RESULTS"
