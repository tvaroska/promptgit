"""

    Representation of repository or subdirectory in repository as prompt storage

"""

from typing import Union

from pathlib import Path
from tempfile import TemporaryDirectory

from git import Repo as DRepo
from git import Blob
from git import InvalidGitRepositoryError

from .prompt import Prompt, PromptLocation

GIT_START = ["git", "https", "http"]


class PromptRepo:
    """
    Prompt repository

    PromptRepo:
        path: location of repo. None means current directory. Remote location on git compatible repo
        history: how many commits to the past to parse,
        name_inference: application/name default inference from directory and filename,
        raise_exception: raise exception if prompt not fount (default) or return None,
        prompt_format: format of variables in the prompts. str (f-string) only
        tag (str): checkout tag for the repo
    """

    def __init__(
        self,
        path: Union[None, str, Path],
        dir: str = None,
        name_inference=PromptLocation.from_dir,
        raise_exception=True,
        prompt_format: str = 'str',
        tag: str = None
    ):
        self.name_inference = name_inference
        self.raise_exception = raise_exception
        # TODO: check validity
        self.prompt_format = prompt_format

        # Remote repo
        # WARNING for https method: if repo does not exists, it will wait for username/password
        if path and any([path.startswith(git) for git in GIT_START]):
            self.tempdir = TemporaryDirectory()
            self.repo = DRepo.clone_from(path, self.tempdir.name)
            self.home = Path(self.tempdir.name)
        else:
            self.tempdir = None
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

            try:
                self.repo = DRepo(path)
            except InvalidGitRepositoryError:
                self.repo = None

        if tag:
            self.tag = tag
            try:
                idx = [t.name for t in self.repo.tags].index(self.tag)
            except ValueError:
                raise ValueError(f'Tag {self.tag} does not exists')
            self.commit = self.repo.tags[idx].commit
        else:
            self.commit = self.repo.head.commit

        self.dir = dir if dir else ''
        self.files = [
            item
            for item in self.commit.tree.traverse()
            if item.type == 'blob' and item.name.split('.')[-1] in ['md', 'txt', 'json'] and item.path.startswith(self.dir)
        ]
        self.prompts = {}
        self.file_names = {}
        for f in self.files:
            prompt = self.parse_file(f)
            if isinstance(f, Blob):
                fname = f.path
            else:
                fname = f.relative_to(self.home)

            location = name_inference(fname)

            # Overide only if prompt.application is None
            prompt.application = (
                location.application
                if not prompt.application
                else prompt.application
            )
            prompt.name = (
                location.name if not prompt.name else prompt.name
            )
            self.file_names[fname] = prompt
            if prompt.application:
                self.prompts[f'{prompt.application}/{prompt.name}'] = prompt
            else:
                self.prompts[f'{prompt.name}'] = prompt

    def __del__(self):
        if self.tempdir:
            del self.tempdir

    def __getitem__(self, location):
        return self.__call__(location)

    def __call__(self, location):
        if location in self.prompts:
            if self.prompt_format == 'str':
                return str(self.prompts[location])
            if self.prompt_format == 'langchain':
                return self.prompts[location].as_langchain()
        else:
            if self.raise_exception:
                raise KeyError(f"Prompt {location} does not exists")
            else:
                return None

    def list_changes(self):
        if not self.repo:
            return None
        head = self.repo.head.commit
        past = head.parents[0]
        changes = past.diff(head)
        changed_files = [
            change.b_path
            for change in changes
            if change.change_type in ['A', 'M']
        ]

        changed_prompts = [self.file_names[f] for f in changed_files]

        return changed_prompts

    def parse_file(self, f: Union[Blob | Path]):
        if isinstance(f, Blob):
            content = f.data_stream.read().decode('utf-8')
            ftype = f.name.split('.')[-1]
        else:
            content = f.read_text()
            ftype = f.suffix[1:]
        if ftype == 'md':
            return Prompt.from_md(content)
        elif ftype == 'json':
            return Prompt.from_json(content)
        elif ftype == 'yaml':
            return Prompt.from_yaml(content)
        else:
            return Prompt.from_text(content)
