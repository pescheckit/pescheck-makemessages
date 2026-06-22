import os
import re
import subprocess
from pathlib import Path

from django.core.management.commands import makemessages
from django.core.management.utils import popen_wrapper

DATE_RE = re.compile(r'^"(POT-Creation-Date|PO-Revision-Date):.*\\n"\s*$', re.MULTILINE)


class Command(makemessages.Command):

    def handle(self, *args, **options):
        # Default to --add-location=file to reduce noisy diffs
        if options.get("add_location") is None:
            options["add_location"] = "file"
        super().handle(*args, **options)

    def find_files(self, root):
        # Skip files that git ignores (e.g. test artifacts) so they don't
        # leak msgids into the .po files.
        return self._drop_gitignored(super().find_files(root))

    def _drop_gitignored(self, files):
        if not files:
            return files

        paths = [f.path for f in files]
        try:
            result = subprocess.run(
                ["git", "check-ignore", "--stdin", "-z"],
                input="\0".join(paths) + "\0",
                capture_output=True,
                text=True,
            )
        except (OSError, FileNotFoundError):
            # git unavailable: leave the file list untouched.
            return files

        # 0 = some paths ignored, 1 = none ignored; anything else (e.g. 128
        # when not in a git repo) means we can't tell, so keep everything.
        if result.returncode not in (0, 1):
            return files

        ignored = {p for p in result.stdout.split("\0") if p}
        return [f for f in files if f.path not in ignored]

    def write_po_file(self, potfile, locale):
        basedir = os.path.join(os.path.dirname(potfile), locale, "LC_MESSAGES")
        pofile = os.path.join(basedir, "%s.po" % self.domain)

        # Save original dates before msgmerge overwrites them.
        original_dates = {}
        if os.path.exists(pofile):
            content = Path(pofile).read_text(encoding="utf-8")
            for match in DATE_RE.finditer(content):
                original_dates[match.group(1)] = match.group(0)

        super().write_po_file(potfile, locale)

        if os.path.exists(pofile):
            # Clear fuzzy flags and empty their msgstr.
            args = ["msgattrib", "--clear-fuzzy", "--empty", "--no-obsolete", "-o", pofile, pofile]
            _, errors, status = popen_wrapper(args)
            if errors and status != 0:
                raise makemessages.CommandError("errors happened while running msgattrib\n%s" % errors)

            # Restore original dates.
            if original_dates:
                content = Path(pofile).read_text(encoding="utf-8")
                for key, original_line in original_dates.items():
                    content = DATE_RE.sub(
                        lambda m: original_line if m.group(1) == key else m.group(0),
                        content,
                    )
                Path(pofile).write_text(content, encoding="utf-8")
