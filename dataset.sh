#!/usr/bin/env bash
DATASET="${DATASET:-clrs}"
DATA_CONFIG="${DATA_CONFIG:-data/clrs/config.yaml}"
case "$DATASET" in
  clrs)
    DATA_FILE="$(python -c 'import sys, yaml; print(yaml.safe_load(open(sys.argv[1]))["output_jsonl"])' "$DATA_CONFIG")"
    DATASET_TAG="$(basename "$DATA_FILE" .jsonl | tr '[:upper:]' '[:lower:]')"
    RESPONSE_FLAGS=(--dataset clrs --dataset_file "$ROOT/$DATA_FILE") ;;
  mmlu-pro)
    DATA_FILE=""
    DATASET_TAG=""
    RESPONSE_FLAGS=(--dataset TIGER-Lab/MMLU-Pro) ;;
  *) echo "unknown DATASET=$DATASET (clrs | mmlu-pro)" >&2; exit 1 ;;
esac
ARTIFACT_ID="${MODEL_ID}${DATASET_TAG:+_${DATASET_TAG}}"
