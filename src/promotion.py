"""Promote staged files with ordinary-exception rollback, not a crash transaction."""
import os
import shutil
import tempfile
from pathlib import Path


def promote(pairs):
    pairs = [(Path(source), Path(target)) for source, target in pairs]
    with tempfile.TemporaryDirectory(prefix='.rollback-', dir=pairs[0][0].parent) as directory:
        backups = []
        installed = []
        for index, (source, target) in enumerate(pairs):
            target.parent.mkdir(parents=True, exist_ok=True)
            backup = Path(directory) / str(index)
            if target.exists():
                shutil.copyfile(target, backup)
            backups.append(backup if backup.exists() else None)
        try:
            for index, (source, target) in enumerate(pairs):
                os.replace(source, target)
                installed.append(index)
        except Exception:
            for index in reversed(installed):
                target = pairs[index][1]
                if backups[index] is None:
                    target.unlink(missing_ok=True)
                else:
                    os.replace(backups[index], target)
            raise
