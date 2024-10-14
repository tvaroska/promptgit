"""

    Representation of repository or subdirectory in repository as prompt storage

"""

from typing import Union

from pathlib import Path

# Refarctor from dulwich to GitPython
from git import Repo as DRepo
from git import Blob
from git import InvalidGitRepositoryError
# from dulwich.repo import Repo as DRepo
# from dulwich.errors import NotGitRepository

from .prompt import PARSERS, FileTypes, Prompt, PromptLocation

GIT_START = ["git", "https", "http"]


class PromptRepo:
    """
    Prompt repository

    PromptRepo:
        path: location of repo. None means current directory
        history: how many commits to the past to parse,
        parsers: dictionary of file parsers (markdown, json and text is default),
        name_inference: application/name default inference from directory and filename,
        raise_exception: raise exception if prompt not fount (default) or return None,
    """

    def __init__(
        self,
        path: Union[None, str, Path],
        history: int =10,
        parsers=PARSERS,
        name_inference=PromptLocation.from_dir,
        raise_exception=True,
    ):
# TODO: handle remote !!!
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
        self.raise_exception = raise_exception

        if any([path.startswith(git) for git in GIT_START]):
            raise NotImplementedError('Remote git repositories are not implemented yet')
        else:
            try:
                self.repo = DRepo(path)
            except InvalidGitRepositoryError:
                self.repo = None

# commit (can be repo.head.commit) .tree.traverse() 
# TODO: handle non-git repos !
        self.files = [
            item
            for item in self.repo.head.commit.tree.traverse()
            if item.type == 'blob' and item.name.split('.')[-1] in ['md', 'txt', 'json']
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
        try:
            parser = PARSERS[FileTypes(ftype)]
        except ValueError:
            # If there is no filetype - let's assume it is pure text
            parser = PARSERS[FileTypes("txt")]
        return Prompt.from_text(content, parser)
