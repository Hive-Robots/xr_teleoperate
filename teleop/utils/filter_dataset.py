#!/usr/bin/env python3
"""
Copy episode folders episode_XXXX from a source directory into a new directory.

Example:
  python copy_episodes.py \
    --src /path/to/dataset_root \
    --init 15 --end 25 \
    --suffix _trimmed

If src basename is "pick_toy_left_dec9_5t_10s", destination will be:
  /path/to/dataset_root_trimmed/
and it will contain:
  episode_0015 ... episode_0025 (copied recursively)
"""
import argparse
import re
import shutil
import sys
from pathlib import Path


EP_RE = re.compile(r"^episode_(\d+)$")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="Source folder containing episode_XXXX subfolders")
    ap.add_argument("--init", type=int, default=0, help="First episode index to copy (inclusive)")
    ap.add_argument("--end", type=int, required=True, help="Last episode index to copy (inclusive)")
    ap.add_argument("--suffix", required=True, help="Suffix appended to src folder name for destination")
    ap.add_argument("--dst_parent", default=None, help="Where to create destination folder (default: parent of --src)")
    ap.add_argument("--overwrite", action="store_true", help="If destination exists, delete it first")
    ap.add_argument("--dry_run", action="store_true", help="Print what would be copied without copying")
    args = ap.parse_args()

    src = Path(args.src).expanduser().resolve()
    if not src.exists() or not src.is_dir():
        print(f"ERROR: --src is not a directory: {src}", file=sys.stderr)
        sys.exit(2)

    if args.init < 0 or args.end < 0 or args.init > args.end:
        print(f"ERROR: invalid range init={args.init}, end={args.end}", file=sys.stderr)
        sys.exit(2)

    dst_parent = Path(args.dst_parent).expanduser().resolve() if args.dst_parent else src.parent
    dst = dst_parent / f"{src.name}{args.suffix}"

    # Prepare destination root
    if dst.exists():
        if args.overwrite:
            if args.dry_run:
                print(f"[DRY RUN] Would delete existing destination: {dst}")
            else:
                shutil.rmtree(dst)
        else:
            print(f"ERROR: destination already exists: {dst}\n"
                  f"Use --overwrite or choose a different --suffix/--dst_parent.",
                  file=sys.stderr)
            sys.exit(2)

    # Collect episode folders
    episodes = []
    for p in src.iterdir():
        if not p.is_dir():
            continue
        m = EP_RE.match(p.name)
        if not m:
            continue
        idx = int(m.group(1))
        episodes.append((idx, p))

    episodes.sort(key=lambda t: t[0])

    # Filter by range
    selected = [(i, p) for (i, p) in episodes if args.init <= i <= args.end]
    if not selected:
        print(f"ERROR: no episode_* folders found in range [{args.init}, {args.end}] under {src}", file=sys.stderr)
        sys.exit(2)

    # Create destination root
    if args.dry_run:
        print(f"[DRY RUN] Would create destination: {dst}")
    else:
        dst.mkdir(parents=True, exist_ok=False)

    # Copy selected episodes
    print(f"Source:      {src}")
    print(f"Destination: {dst}")
    print(f"Copying episodes {args.init}..{args.end} (inclusive): {len(selected)} folder(s)\n")

    for idx, ep_path in selected:
        out_path = dst / ep_path.name
        if args.dry_run:
            print(f"[DRY RUN] Would copy: {ep_path} -> {out_path}")
        else:
            shutil.copytree(ep_path, out_path)

    print("\nDone.")


if __name__ == "__main__":
    main()
