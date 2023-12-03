from dataclasses import dataclass


@dataclass
class RestorePoint:
    string: list[str]
    stack: list[str]
    path: list[str]
