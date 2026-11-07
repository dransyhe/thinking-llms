import argparse
import json
import os
import zlib

import numpy as np
import yaml

from data.clrs.samplers import SAMPLERS
from data.clrs.templates import FAMILIES, TEMPLATES, render, serialise

CONFIG_KEYS = {"seed", "n_per_algorithm", "float_decimals", "matrix_dimension_scale", "require_connected_graphs",
               "reject_duplicate_questions", "max_rejections", "output_jsonl", "lengths"}


def load_config(path):
    with open(path) as f:
        cfg = yaml.safe_load(f)
    if set(cfg) != CONFIG_KEYS:
        raise ValueError(f"{path}: expected keys {sorted(CONFIG_KEYS)}, got {sorted(cfg)}")
    if set(cfg["lengths"]) != set(SAMPLERS) or set(TEMPLATES) != set(SAMPLERS) or set(FAMILIES) != set(SAMPLERS):
        raise ValueError(f"{path}: lengths, templates and families must cover exactly {sorted(SAMPLERS)}")
    return cfg


def connected(inputs):
    """Every node is reachable from the source, or for source-less algorithms the graph is weakly connected."""
    adj = np.asarray(inputs[0]) != 0
    source = int(inputs[1]) if len(inputs) > 1 else 0
    if len(inputs) == 1:
        adj |= adj.T
    reached, frontier = {source}, {source}
    while frontier:
        frontier = {int(v) for u in frontier for v in np.flatnonzero(adj[u])} - reached
        reached |= frontier
    return len(reached) == len(adj)


def draw_problem(algorithm, sampler, length, template_id, cfg, seen):
    for _ in range(cfg["max_rejections"]):
        inputs = sampler.sample(length)
        question = render(algorithm, inputs, template_id, cfg)
        valid_graph = not cfg["require_connected_graphs"] or FAMILIES[algorithm] != "graphs" or connected(inputs)
        if valid_graph and not (cfg["reject_duplicate_questions"] and question in seen):
            seen.add(question)
            return inputs, question
    raise RuntimeError(f"{algorithm} length {length}: no acceptable sample after {cfg['max_rejections']} draws")


def algorithm_rows(algorithm, cfg, first_id):
    key = zlib.crc32(algorithm.encode())
    meta_rng = np.random.RandomState([cfg["seed"], key, 0])
    sampler = SAMPLERS[algorithm](np.random.RandomState([cfg["seed"], key, 1]), cfg["float_decimals"])
    rows, seen = [], set()
    for i in range(cfg["n_per_algorithm"]):
        length = int(meta_rng.choice(cfg["lengths"][algorithm]))
        template_id = int(meta_rng.randint(len(TEMPLATES[algorithm])))
        inputs, question = draw_problem(algorithm, sampler, length, template_id, cfg, seen)
        rows.append({"question_id": first_id + i, "algorithm": algorithm, "category": algorithm,
                     "family": FAMILIES[algorithm], "template_id": template_id, "length": length,
                     "question": question, "inputs": serialise(inputs)})
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    cfg = load_config(parser.parse_args().config)
    rows = [row for k, algorithm in enumerate(SAMPLERS)
            for row in algorithm_rows(algorithm, cfg, k * cfg["n_per_algorithm"])]
    os.makedirs(os.path.dirname(cfg["output_jsonl"]), exist_ok=True)
    with open(cfg["output_jsonl"], "w") as f:
        f.writelines(json.dumps(row) + "\n" for row in rows)
    print(f"Wrote {len(rows)} problems for {len(SAMPLERS)} algorithms to {cfg['output_jsonl']}")


if __name__ == "__main__":
    main()
