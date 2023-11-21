import typing
from Nonterminal import Nonterminal
import re

class Parser:

    nonterminals: dict[str, Nonterminal]
    NT_RULE=r"<(?P<nonterminal>[a-z_]+)>: (?P<rules>.*)?"
    NT_OR_RULE=r"\t\| (?P<rules>.+)"

    def __init__(self) -> None:
        self.nonterminals={}

    @classmethod
    def from_file(cls, filename)->typing.Self:
        instance=Parser()
        with open(filename) as file:
            current_ruleset:list[str]=[]
            current_nonterminal=None
            for line in file.readlines():
                nonterminal, rules=instance._parse_string(line)
                if nonterminal:
                    if current_nonterminal:
                        instance.nonterminals[nonterminal]=Nonterminal(current_nonterminal, current_ruleset)
                    current_nonterminal=nonterminal
                    current_ruleset=rules.copy()
                else:
                    current_ruleset+=rules.copy()
                


    def _parse_string(self, string:str) -> tuple[str|None, list[str]|None]:
        found = re.match(self.NT_RULE, string)
        if found:
            rules=found.group('rules').split('|')
            return found.group('nonterminal'), rules
        found =  re.match(self.NT_OR_RULE, string)
        if found:
            return None, found.group('rules').split('|')
        raise ValueError(f'cannot parse string {string}')