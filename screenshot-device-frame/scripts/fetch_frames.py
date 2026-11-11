#!/usr/bin/env python3
"""Fetch frameit bezels on demand (transparent PNG) into frames/.

  python3 fetch_frames.py --list            # list remote bezels
  python3 fetch_frames.py 17promax 16pro    # download by alias
  python3 fetch_frames.py --search "iPhone 17"

Shares aliases / pin / download logic with bezel.py so they never drift.
"""
import argparse, json, sys, urllib.parse, urllib.request

from bezel import ALIAS, BASE, FDIR, VER, fetch

API = "https://api.github.com/repos/fastlane/frameit-frames/contents/" + VER


def remote_listing():
    req = urllib.request.Request(API, headers={"User-Agent": "fetch-frames"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return [x["name"] for x in json.load(r) if x["name"].lower().endswith(".png")]


def main():
    ap = argparse.ArgumentParser(description="download frameit bezels")
    ap.add_argument("devices", nargs="*", help="alias or bezel filename")
    ap.add_argument("--list", action="store_true", help="list all remote bezels")
    ap.add_argument("--search", help="filter remote list by keyword")
    a = ap.parse_args()

    if a.list or a.search:
        names = remote_listing()
        if a.search:
            names = [n for n in names if a.search.lower() in n.lower()]
        for n in names:
            print(n)
        print("\n%d bezels (build %s)" % (len(names), VER))
        print("aliases: " + ", ".join(sorted(ALIAS)))
        return

    if not a.devices:
        ap.print_help()
        print("\naliases: " + ", ".join(sorted(ALIAS)))
        return

    for d in a.devices:
        name = ALIAS.get(d.lower())
        if name is None:
            if d.lower().endswith(".png"):
                name = d
            else:
                print("unknown alias %r - pass a .png filename or use --search" % d,
                      file=sys.stderr)
                print("aliases: " + ", ".join(sorted(ALIAS)), file=sys.stderr)
                continue
        fetch(name)
        print("OK %s -> %s" % (d, name))


if __name__ == "__main__":
    main()
