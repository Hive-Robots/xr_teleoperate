#!/usr/bin/env python3
"""
Use this to check that non-zero values are recorded for the end-effector states and actions
Compute min, max, and range for EE and arm states/actions from a Unitree JSON dataset.
"""

import json
import numpy as np
import argparse

def extract_values(entries, section, part_key, field="qpos"):
    """
    Extract arrays (e.g. qpos) from either 'states' or 'actions' for a given part.
    Returns a NumPy array of shape (N, D) if data exists, else None.
    """
    all_vals = []

    for item in entries:
        try:
            q = item[section][part_key][field]
            if q:
                all_vals.append(q)
        except KeyError:
            continue

    if not all_vals:
        return None

    return np.array(all_vals, dtype=float)


def summarize(name, arr):
    """
    Print min, max, and range for an array.
    """
    print(f"\n=== {name} ===")
    print("Min:   ", np.min(arr, axis=0))
    print("Max:   ", np.max(arr, axis=0))
    print("Range: ", np.max(arr, axis=0) - np.min(arr, axis=0))


def main():
    parser = argparse.ArgumentParser(description="Check EE and arm value ranges in dataset JSON.")
    parser.add_argument("json_path", type=str, help="Path to JSON dataset")
    args = parser.parse_args()

    # Load dataset
    with open(args.json_path, "r") as f:
        dataset = json.load(f)

    entries = dataset["data"]

    # Parts to analyze (qpos only)
    parts = ["left_ee", "right_ee", "left_arm", "right_arm"]

    for section in ["states", "actions"]:
        for part in parts:
            arr = extract_values(entries, section, part, field="qpos")
            if arr is not None:
                summarize(f"{part} {section}", arr)


if __name__ == "__main__":
    main()
