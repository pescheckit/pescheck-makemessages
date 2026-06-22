# pescheck-makemessages

Custom Django `makemessages` command with sane defaults for translation workflows.

## What it does

- **Defaults to `--add-location=file`** — only stores filenames in `.po` comments, not line numbers, so moving code around doesn't bloat diffs
- **Clears fuzzy entries** — Django silently ignores fuzzy translations at runtime, so they look translated but aren't. This command clears the fuzzy flag and empties the `msgstr`, making untranslated strings visible
- **Preserves date headers** — `POT-Creation-Date` and `PO-Revision-Date` are restored after `msgmerge`, avoiding noisy diffs on every run
- **Skips git-ignored files** — files ignored by git (e.g. test artifacts under `tests/artifacts/`) are excluded, so their strings don't leak into `.po` files. Falls back to scanning everything when git is unavailable or the project isn't a git repo

## Installation

```bash
pip install pescheck-makemessages
```

Add to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...
    "pescheck_makemessages",
]
```

## Usage

```bash
./manage.py make_messages -a
```

All standard `makemessages` flags work as usual.
