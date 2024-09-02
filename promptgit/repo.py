"""

    Representation of repository or subdirectory in repository as prompt storage

"""

from typing import Union

from pathlib import Path

from dulwich.repo import Repo as DRepo
from dulwich.errors import NotGitRepository

from .prompt import PARSERS, FileTypes, Prompt, PromptLocation

GIT_START = ["git", "https", "http"]


class PromptRepo:
    """
    Prompt repository

    PromptRepo:
        path: location of repo. None means current directory
    """

    def __init__(
        self,
        path: Union[None, str, Path],
        history: int =10,
        parsers=PARSERS,
        name_inference=PromptLocation.from_dir,
        overide=False,
        raise_exception=True,
    ):
        if not path:
            self.home = Path.cwd()
        elif isinstance(path, Path):
            self.home = path
        else:
            self.home = Path(path)

        if not self.home.exists():
            raise FileExistsError(f"Directory {str(self.home)} does not exists")
        if not self.home.is_dir():
            raise ValueError(f"{str(self.home)} is not a directory")

        self.parsers = parsers
        self.name_inference = name_inference
        self.overide = overide
        self.raise_exception = raise_exception

        if any([path.startswith(git) for git in GIT_START]):
            raise NotImplementedError
        else:
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
        self.file_names = {}
        for f in self.files:
            prompt = self.parse_file(f)
            location = name_inference(f.relative_to(self.home))

            # Overide only if prompt.application is None or overide is True
            # ,otherwise keep
            prompt.application = (
                location.application
                if not prompt.application or overide
                else prompt.application
            )
            prompt.name = (
                location.name if not prompt.name or overide else prompt.name
            )
            self.file_names[str(f.relative_to(self.home))] = prompt
            self.prompts[str(prompt.location)] = prompt


    # Get string version of prompt
    # repo(location)
    # repo[location]
    def __getitem__(self, location):
        return self.__call__(location)

    def __call__(self, location):
        if location in self.prompts:
            return str(self.prompts[location])
        else:
            if self.raise_exception:
                raise KeyError(f"Prompt {location} does not exists")
            else:
                return None

    def list_changes(self):
        if not self.repo:
            return None
        last_commit = self.commits[0]
        changed_files = [
            change.new.path
            for change in last_commit.changes()
            if change.type != "delete"
        ]

        changed_prompts = [self.file_names[f.decode()] for f in changed_files]

        return changed_prompts

    def parse_file(self, f: Path):
        content = f.read_text()
        try:
            parser = PARSERS[FileTypes(f.suffix[1:])]
        except ValueError:
            # If there is no filetype - let's assume it is pure text
            parser = PARSERS[FileTypes("txt")]
        return Prompt.from_text(content, parser)
