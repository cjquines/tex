# tex

LaTeX repo for articles, problem sets, and writeups.

## Shell / build gotchas

- zsh has `noclobber` set: `>` to an existing file errors with "file exists". Use `>|` to force, or `rm` first.
- Empty globs (e.g. `rm -f foo/*.tex` when empty) abort the line under `nomatch`. Guard with `mkdir -p` + skip rm, or use `setopt null_glob` locally.
- `latexmk` uses lualatex (`~/.latexmkrc`) and exits non-zero (12) on missing-glyph warnings even when the PDF is produced — check `Output written` in the log, not the exit code.
- `articles/*/problems/*.tex` are AoPS-imported verbatim and contain BBcode-era artifacts (`\plus{}`, `\minus{}`, `:wallbash_:`, stray `&` in URLs) that throw `! Undefined control sequence` per file. These are pre-existing and harmless — confirm `Output written` and page count, don't try to "fix" them unless asked.

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
- Canonical output is run through `bbcode_to_tex()`: `[b]/[i]/[u]→\textbf/\textit/\underline`, `[hide]/[quote]/[color]/[size]/[center]` content kept, `[code]→\texttt`, `[url=…]→\href`, `[list]/[*]→itemize`/`enumerate`. Unknown tags stripped.

### dump_aops_problems.py

Bulk-fetches AoPS URLs into one `.tex` per problem. Filename derived from the thread's `source` (or `topic_title`) field, HTML-entities decoded and accents stripped.

```
python3 tools/dump_aops_problems.py --outdir DIR URL [URL ...]
```

- Problem = post #1; solution = the linked post if non-#1, else the first ≤3 substantive replies (≥80 chars, not a "bump").
- Escapes TeX specials in usernames/source/title so e.g. `v_Enhance` doesn't blow up in math mode.

### aops_contests.py

Walks the AoPS contest archive (rooted at `c13`). The contest hierarchy is not in any page's `bootstrap_data` — it's loaded via the undocumented POST endpoint `/m/community/ajax.php` (`a=fetch_category_data`). One call returns a category's metadata + items; for `view_posts` leaves (a single contest), it returns every problem inline with LaTeX source.

```
python3 tools/aops_contests.py list <id>
python3 tools/aops_contests.py tree <id> [--depth N] [--into-contests]
python3 tools/aops_contests.py urls <id>                # recurse, print problem topic urls
python3 tools/aops_contests.py dump <id> --outdir DIR   # view_posts → one .tex/problem (with solutions; --problem-only for fast bulk)
```

- Bootstraps an anonymous session by scraping `AoPS.session.id` from `c13` once per run; the server ignores `category_type` (just needs the id).
- `fetch_category` auto-paginates: the server returns items 50-at-a-time and signals more via `no_more_items: false` plus cursor fields (`last_item_text/score/level`); the function loops on `fetch_more_items` and dedupes by `item_id` until the server says it's done. So `list 59` returns all ~70 TSTs (was capped at 50 before).
- Pipe `urls <year-folder-id>` into `dump_aops_problems.py` to get problems + solutions across a whole year.
- Useful starting ids: `13` (all contests), `4652593` (2026), `4148541` (2025), `3752401` (2024), `3296298` (2023), `58` (National Olympiads), `59` (TSTs), `14` (International). For TSTs: `3411` (USA TST), `3424` (USA TSTST), `3315053` (Russian TSTs), `3282` (China), `3321` (Iran), `3306` (HK), `4678116` (Japan), `3429` (ELMO), `3430` (ELMO SL), `3223` (IMO SL), `3238` (RMM + RMM SL). For other contests: `3225` (Balkan MO), `915845` (Balkan SL), `3227` (JBMO), `3240` (JBMO SL), `3246` (EGMO), `3239` (Tournament of Towns), `3384` (Korea Final Round), `3383` (Korea NO), `603052` (Korea Junior), `4675505` (Japan MO Finals), `3277` (Canada NO), `1231801` (Canada Junior), `3317` (Indonesia MO), `3273` (Brazil NO).
- Dumped problems live in `~/reading/math/competitive/aops-dumps/<contest-slug>/` for reuse across projects.
- Picking between `aops_contests.py dump` and `dump_aops_problems.py`: the former enumerates a `view_posts` contest in one AJAX call, then by default fetches each thread for problem + first 1-3 substantive solutions (same format as `articles/*/problems/*.tex`) — use this to seed `~/reading/.../aops-dumps/<contest>/`. Pass `--problem-only` to skip the per-thread fetches when you just want grep-fodder. The latter takes explicit topic URLs and produces the same per-problem format — reach for it when adding a single problem to an article. Get its URL from a dumped file's `Link:` line; guessing topic IDs writes a junk file named `error-…`.
- Grepping across dumps: `tail -n +5 file.tex` strips the `\subsection*` / `Source:` / `Link:` / blank-line header so the contest name (e.g. "Tournament of Towns") doesn't generate false positives for keywords that overlap with contest titles.
