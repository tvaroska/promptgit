"""

    Core prompt object

"""

import json
import string

from enum import Enum
from typing import Callable, Dict, List, Optional, Union, NamedTuple
from types import MappingProxyType
from pathlib import Path
from pydantic import BaseModel, field_validator


class FileTypes(str, Enum):
    """
    Supported file types to store prompts
    """

    TXT = "txt"
    MARKDOWN = "md"
    JSON = "json"
    # TODO
    # YAML = "yaml"




MULTI_LINE = ["prmpt", "description"]


class PromptLocation(NamedTuple):
    """
    'Location' of a prompt
    application/prompt name
    """

    application: str
    name: str

    @classmethod
    def from_dir(cls, path):
        p = Path(path)

        return cls(
            application=p.parts[-2] if len(p.parts) > 1 else None, name=p.stem
        )

    @classmethod
    def from_str(cls, location):
        splits = location.split("/")
        if len(splits) == 1:
            application = None
            name = location
        elif len(splits) == 2:
            application = splits[0]
            name = splits[1]
        else:
            raise ValueError

        return cls(application=application, name=name)

    def __str__(self):
        if self.application:
            return f"{self.application}/{self.name}"
        else:
            return f"{self.name}"


def parse_txt(text) -> Dict:
    return {"prompt": text}


def parse_json(text) -> Dict:
    return json.loads(text)


def parse_md(text: str) -> Dict:
    current_section = None
    content = {}

    def safe_add(data, key, line):
        if key in data:
            if isinstance(data[key], str):
                data[key] = data[key] + "\n" + line
            elif isinstance(data[key], list):
                data[key].append(line)
            else:
                raise NotImplementedError
        else:
            if key in "models":
                data[key] = [line]
            else:
                data[key] = line
        return data

    def standardize_sections(key: str) -> str:
        return (
            key.replace("#", "")
            .strip()
            .lower()
            .replace(" ", "_")
            .replace("-", "_")
        )

    for line in text.splitlines():
        if line.strip() == "":
            if current_section and current_section in MULTI_LINE:
                content = safe_add(content, current_section, line)
                continue
            else:
                continue
        if line[0] == "#":
            current_section = standardize_sections(line)
            continue
        if not current_section:
            current_section = "prompt"
        if current_section in content:
            content[current_section] = content[current_section] + "\n" + line
        else:
            content[current_section] = line

    return content


PARSERS = MappingProxyType({
    FileTypes.TXT: parse_txt,
    FileTypes.JSON: parse_json,
    FileTypes.MARKDOWN: parse_md,
})


class Prompt(BaseModel):
    """Core prompt object

    Parameters:
        prompt (str): content of the prompt
    """

    prompt: str
    models: Union[str, List[str]] = []
    description: Optional[str] = None
    application: Optional[str] = None
    name: Optional[str] = None
    use_case: Optional[str] = None
    variables: Optional[List[str]] = None

    @field_validator("models")
    @classmethod
    def convert_single(cls, models: Union[str, List[str]]) -> List[str]:
        if isinstance(models, str):
            return [models]
        else:
            return models

    @classmethod
    def from_text(cls, content: str, parser: Callable = parse_txt):
        """Create object from text string

        Args:
            content (str): _description_
            type (Optional[str], optional): _description_. Defaults to None.

        Returns:
            _type_: _description_
        """
        all_fields = parser(content)

        all_fields["variables"] = {
            v for _, v, _, _ in string.Formatter().parse(all_fields["prompt"]) if v is not None
        }


        return cls(**all_fields)

    def __str__(self):
        return self.prompt

    @property
    def location(self):
        return PromptLocation(application=self.application, name=self.name)
