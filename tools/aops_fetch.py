#!/usr/bin/env python3
"""Fetch posts from an AoPS thread URL.

Given a community URL like https://artofproblemsolving.com/community/c6h356076p29502580,
prints the first post of the thread and the linked post, plus optional context posts
on either side of the linked post.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from html.parser import HTMLParser

URL_RE = re.compile(r"/community/c(\d+)h(\d+)p(\d+)")
BOOTSTRAP_RE = re.compile(r"AoPS\.bootstrap_data\s*=\s*(\{.*?\});", re.DOTALL)
USER_AGENT = "Mozilla/5.0 (aops_fetch.py)"


def fetch_html(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_bootstrap(html: str) -> dict:
    m = BOOTSTRAP_RE.search(html)
    if not m:
        raise ValueError("bootstrap_data not found in page")
    return json.loads(m.group(1))


def post_url(category_id: int, topic_id: int, post_id: int) -> str:
    return f"https://artofproblemsolving.com/community/c{category_id}h{topic_id}p{post_id}"


class _Stripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data):
        self.parts.append(data)

    def handle_starttag(self, tag, attrs):
        if tag == "br":
            self.parts.append("\n")

    def handle_startendtag(self, tag, attrs):
        if tag == "br":
            self.parts.append("\n")


def strip_html(s: str) -> str:
    p = _Stripper()
    p.feed(s)
    return "".join(p.parts)


def format_post(post: dict, category_id: int, topic_id: int, *, raw: bool) -> str:
    body = post["post_canonical"] if not raw else post["post_rendered"]
    url = post_url(category_id, topic_id, post["post_id"])
    header = f"#{post['post_number']} by {post['username']}  {url}"
    return f"{header}\n{body}"


def collect_posts(
    url: str, context: int
) -> tuple[list[dict], int, int]:
    """Return (posts_to_print, category_id, topic_id), posts ordered by post_number."""
    m = URL_RE.search(url)
    if not m:
        raise ValueError(f"unrecognized AoPS URL: {url}")
    category_id, topic_id, _ = map(int, m.groups())

    html = fetch_html(url)
    data = parse_bootstrap(html)
    pd = data["preload_cmty_data"]
    linked_id = pd["post_id"]
    linked_number = pd["post_id_data"]["post_number"]
    first_post_id = pd["topic_data"]["first_post_id"]

    by_id: dict[int, dict] = {p["post_id"]: p for p in pd["topic_data"]["posts_data"]}

    wanted_numbers = {1} | {
        n for n in range(linked_number - context, linked_number + context + 1) if n >= 1
    }

    by_number = {p["post_number"]: p for p in by_id.values()}
    missing = wanted_numbers - by_number.keys()

    # If the first post isn't in the current page, fetch it directly.
    if 1 in missing and first_post_id not in by_id:
        extra_html = fetch_html(post_url(category_id, topic_id, first_post_id))
        extra = parse_bootstrap(extra_html)["preload_cmty_data"]["topic_data"]["posts_data"]
        for p in extra:
            by_id.setdefault(p["post_id"], p)
            by_number.setdefault(p["post_number"], p)

    selected = [by_number[n] for n in sorted(wanted_numbers) if n in by_number]
    return selected, category_id, topic_id


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("url", help="AoPS post URL (c<cat>h<topic>p<post>)")
    ap.add_argument(
        "-c", "--context", type=int, default=0,
        help="number of posts to fetch on either side of the linked post (default 0)",
    )
    ap.add_argument(
        "--raw", action="store_true",
        help="print rendered HTML rather than canonical LaTeX form",
    )
    ap.add_argument(
        "--strip-html", action="store_true",
        help="with --raw, strip HTML tags from the output",
    )
    args = ap.parse_args(argv)

    posts, cat, topic = collect_posts(args.url, args.context)
    chunks = []
    for p in posts:
        s = format_post(p, cat, topic, raw=args.raw)
        if args.raw and args.strip_html:
            s = strip_html(s)
        chunks.append(s)
    print("\n\n---\n\n".join(chunks))
    return 0


if __name__ == "__main__":
    sys.exit(main())
