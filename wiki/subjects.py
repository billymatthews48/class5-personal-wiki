"""Load subjects.yaml and map raw files to the subject note they feed."""
from dataclasses import dataclass
from pathlib import PurePosixPath

import yaml

from . import config


@dataclass
class Subject:
    key: str
    title: str
    folder: str
    sources: list

    @property
    def note_path(self):          # vault-relative
        return f"wiki/{self.folder}/{self.title}.md"


def load():
    data = yaml.safe_load(config.SUBJECTS_FILE.read_text(encoding="utf-8"))
    return [Subject(**s) for s in data["subjects"]]


def subject_for(raw_path, subjects):
    p = PurePosixPath(raw_path)
    for s in subjects:
        if any(p.full_match(pattern) for pattern in s.sources):
            return s
    return None
