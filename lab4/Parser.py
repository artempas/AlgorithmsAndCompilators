import typing
from Nonterminal import Nonterminal
import re


class Parser:
    nonterminals: dict[str, Nonterminal]
    NT_RULE = r"<(?P<nonterminal>[a-z_]+)>: (?P<rules>.*)?"
    NT_OR_RULE = r"\t\| (?P<rules>.+)"

    def __init__(self) -> None:
        self.nonterminals = {}

    @classmethod
    def from_file(cls, filename) -> typing.Self:
        instance = Parser()
        with open(filename) as file:
            current_ruleset: list[str] = []
            current_nonterminal = None
            is_first = True
            for line in file.readlines():
                new_nonterminal, rules = instance._parse_string(line)
                if new_nonterminal:
                    if current_nonterminal:
                        instance.nonterminals[current_nonterminal] = Nonterminal(current_nonterminal, current_ruleset,
                                                                                 is_first)
                        if is_first:
                            is_first = False
                    current_nonterminal = new_nonterminal
                    current_ruleset = rules.copy() if rules else []
                else:
                    current_ruleset += rules.copy()
            instance.nonterminals[current_nonterminal] = Nonterminal(current_nonterminal, current_ruleset, is_first)
        return instance

    def print_all_firsts(self):
        for key, nonterminal in self.nonterminals.items():
            print(f"FIRST({key}) => {nonterminal.first(self.nonterminals)}")

    def print_all_follows(self):
        for key, nonterminal in self.nonterminals.items():
            print(f"FOLLOW({key}) => {nonterminal.follow(self.nonterminals)}")

    def _parse_string(self, string: str) -> tuple[str | None, list[str] | None]:
        """
        Picks nonterminal and rules from string. Returns list of raw expressions
        :param string:
        :return:
        """
        found = re.match(self.NT_RULE, string)
        if found:
            rule_str=found.group('rules')
            rules = rule_str.split('|') if rule_str else None
            return found.group('nonterminal'), rules
        found = re.match(self.NT_OR_RULE, string)
        if found:
            return None, found.group('rules').split('|')
        raise ValueError(f'cannot parse string {string}')
