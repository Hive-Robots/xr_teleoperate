#!/usr/bin/env python3
"""
Cut a Unitree-style episode into a new episode folder.

Example:
  python cut_episode.py --task-dir /path/to/task_dir --episode 12 --start 100 --end 300 --out-episode 1012
Creates:
  /path/to/task_dir/episode_1012/...
"""

import argparse
import json
import shutil
from pathlib import Path


def load_json(p: Path) -> dict:
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(p: Path, obj: dict) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)


def copy_rel_file(src_ep_dir: Path, dst_ep_dir: Path, rel_path: str) -> str:
    """Copy a file referenced by rel_path into dst episode, preserving subfolders."""
    src = src_ep_dir / rel_path
    if not src.exists():
        return rel_path  # keep as-is; caller can decide whether to error
    dst = dst_ep_dir / rel_path
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return rel_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task-dir", required=True, type=str)
    ap.add_argument("--episode", required=True, type=int, help="Input episode index (e.g. 12 -> episode_0012)")
    ap.add_argument("--start", required=True, type=int, help="Start frame index (0-based) in data.json['data']")
    ap.add_argument("--end", required=True, type=int, help="End frame index (exclusive)")
    ap.add_argument("--out-episode", required=True, type=int, help="Output episode index (e.g. 1012 -> episode_1012)")
    ap.add_argument("--keep-idx", action="store_true",
                    help="Keep original 'idx' values. By default reindexes idx to 0..N-1.")
    args = ap.parse_args()

    task_dir = Path(args.task_dir)
    src_ep = task_dir / f"episode_{args.episode:04d}"
    dst_ep = task_dir / f"episode_{args.out_episode:04d}"

    src_json = src_ep / "data.json"
    if not src_json.exists():
        raise FileNotFoundError(f"Missing {src_json}")

    j = load_json(src_json)
    frames = j.get("data", [])
    if not frames:
        raise ValueError("No frames under 'data'.")

    start = max(0, args.start)
    end = min(len(frames), args.end)
    if end <= start:
        raise ValueError(f"Invalid range: start={start}, end={end}, len={len(frames)}")

    cut = frames[start:end]

    # Copy files referenced in colors/depths/audios
    dst_ep.mkdir(parents=True, exist_ok=True)

    for fr in cut:
        for section in ("colors", "depths", "audios"):
            sec = fr.get(section, {}) or {}
            for k, rel in list(sec.items()):
                if not rel:
                    continue
                # Paths in your json are usually like "colors/000000_color_0.jpg"
                copy_rel_file(src_ep, dst_ep, rel)

    # Optionally reindex idx
    if not args.keep_idx:
        for i, fr in enumerate(cut):
            fr["idx"] = i

    # Write new json
    out = dict(j)
    out["data"] = cut
    save_json(dst_ep / "data.json", out)

    print(f"Written cut episode: {dst_ep}")
    print(f"Frames: {len(cut)}  (from [{start}:{end}))")


if __name__ == "__main__":
    main()
