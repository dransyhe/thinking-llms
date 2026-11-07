#!/usr/bin/env bash
#SBATCH --job-name=train-saes-qwen3-4b-instruct-sweep
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

# The paper's layer sweep (train-saes/run.sh get_layers) for Qwen/Qwen3-4B-Instruct-2507:
# 6 layers evenly spaced through its 36 layers with a constant step (~total/8, here 5), the same
# 14%-83% depth range the paper uses for its 28- and 64-layer models. Everything else, including
# the cluster size (30) and the labelling of every layer, comes from train_saes_qwen3_4b_instruct.sh,
# which reuses the responses (and any cached activations) already on disk.
#
#   sbatch --dependency=afterany:<middle-layer job id> train_saes_qwen3_4b_instruct_sweep.sh

set -euo pipefail
cd /scr/heyu/thinking-llms
LAYERS="${LAYERS:-5 10 15 20 25 30}" bash train_saes_qwen3_4b_instruct.sh
