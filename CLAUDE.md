# tex

LaTeX repo for articles, problem sets, and writeups.

## tools/

Python scripts (stdlib only, Python 3.14+). Run directly with `python3`.

### aops_fetch.py

Fetches posts from an AoPS thread URL by parsing `AoPS.bootstrap_data` from the page.

```
python3 tools/aops_fetch.py <url> [-c CONTEXT] [--raw [--strip-html]]
```

- Always prints the thread's first post and the linked post.
- `-c N` adds N posts on either side of the linked post.
- Defaults to `post_canonical` (LaTeX source); `--raw` uses `post_rendered` (HTML).
- Falls back to a second fetch via the first post's permalink when the first post isn't in the linked post's page window.
