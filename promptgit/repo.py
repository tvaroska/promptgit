from pathlib import Path

from dulwich.repo import Repo as DRepo
from dulwich.errors import NotGitRepository

from .prompt import PARSERS, FileTypes, Prompt, PromptLocation

class PromptRepo:
    def __init__(self, path, history=10, parsers=PARSERS, name_inference = PromptLocation.from_dir, overide = False, raise_exception = True):
        self.home = Path(path)
        self.parsers = parsers
        self.name_inference = name_inference
        self.overide = overide
        self.raise_exception = raise_exception

        try:
            self.repo = DRepo(path)
            self.commits = list(self.repo.get_walker(max_entries=history))
        except NotGitRepository:
            self.repo = None

        self.files = [
            p
            for p in self.home.rglob("*")
            if p.is_file()
            and not any(
                [part[0] == "." for part in p.parts]
            )  # Filter any hidden directories
        ]
        self.prompts = {}
        for f in self.files:
            prompt = self.parse_file(f)
            location = name_inference(f.relative_to(self.home))

            # Overide only if prompt.application is None or overide is True, otherwise keep
            prompt.application = location.application if not prompt.application or overide else prompt.application
            prompt.name = location.name if not prompt.name or overide else prompt.name
            self.prompts[str(prompt.location)] = prompt

    def __call__(self, location):
        if location in self.prompts:
            return str(self.prompts[location])
        else:
            if self.raise_exception:
                raise KeyError(f'Prompt {location} does not exists')
            else:
                return None

    def parse_file(self, f: Path):
        content = f.read_text()
        try:
            parser = PARSERS[FileTypes(f.suffix[1:])]
        except ValueError:
            # If there is no filetype - let's assume it is pure text
            parser = PARSERS[FileTypes("txt")]
        return Prompt.from_text(content, parser)
