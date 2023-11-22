import typing
from logging import getLogger
from prettytable import PrettyTable

from Nonterminal import Nonterminal, Token, Rule
import re

logger = getLogger('Parser')


class Parser:
    nonterminals: dict[str, Nonterminal]
    NT_RULE = r"<(?P<nonterminal>[a-z_]+)>: (?P<rules>.*)?"
    NT_OR_RULE = r"\t\| (?P<rules>.+)"
    parsing_table: dict[Token, dict[Token, Rule]]
    syntax_analysis_table: dict[Token, dict[Token, Rule]]

    def __init__(self) -> None:
        self.syntax_analysis_table = {}
        self.parsing_table = {}
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
        instance.__build_parsing_table()
        return instance

    def print_all_firsts(self):
        for key, nonterminal in self.nonterminals.items():
            logger.info(f"FIRST({key}) => {nonterminal.first(self.nonterminals)}")

    def print_all_follows(self):
        for key, nonterminal in self.nonterminals.items():
            logger.info(f"FOLLOW({key}) => {nonterminal.follow(self.nonterminals)}")

    def _parse_string(self, string: str) -> tuple[str | None, list[str] | None]:
        """
        Picks nonterminal and rules from string. Returns list of raw expressions
        :param string:
        :return:
        """
        found = re.match(self.NT_RULE, string)
        if found:
            rule_str = found.group('rules')
            rules = rule_str.split('|') if rule_str else None
            return found.group('nonterminal'), rules
        found = re.match(self.NT_OR_RULE, string)
        if found:
            return None, found.group('rules').split('|')
        raise ValueError(f'cannot parse string {string}')

    def __build_parsing_table(self) -> None:
        table: dict[Token, dict[Token, Rule]] = {}  # [nonterminal][terminal
        for nonterminal in self.nonterminals.values():
            table[nonterminal.token] = {}
            for rule in nonterminal.rules:
                first = Nonterminal.first_for_rule(rule, self.nonterminals)
                if '@' not in first:
                    for terminal in first:
                        table[nonterminal.token][terminal] = rule
                else:
                    raise NotImplementedError("Haven't done for @ in first")
        self.parsing_table = table

    @property
    def terminals(self):
        terminals = set()
        for i in self.nonterminals.values():
            terminals = terminals.union(i.get_terminals())
        return terminals
    def print_table(self, table: dict[Token, dict[Token, Rule]], save_to_csv: str = None):
        terminals = sorted(list(self.terminals))
        pt = PrettyTable()
        pt.field_names = [""] + [terminal.text for terminal in terminals]
        for nonterminal in table:
            row = [f"<{nonterminal.text}>"] + [
                str(table[nonterminal].get(terminal)) for terminal in terminals
            ]
            pt.add_row(row)
        print(pt)
        if save_to_csv:
            with open(save_to_csv, 'w', newline='') as file:
                file.write(pt.get_csv_string())

    def add_sync(self):
        self.syntax_analysis_table = self.parsing_table.copy()
        for nonterminal in self.nonterminals.values():
            for terminal in nonterminal.follow(self.nonterminals):
                self.syntax_analysis_table[nonterminal.token][terminal] = Rule(sync=True)
            for terminal in nonterminal.first(self.nonterminals):
                self.syntax_analysis_table[nonterminal.token][terminal].sync = True

    def test_string(self, string: str) -> list[str]:
        """
        Parses string, returns errors
        """
        stack = [Token(False, '$'), Token(True, 'program')]
        errors = []
        position = 0
        in_panic = False
        while position < len(string):
            next_terminal=None
            try:
                next_terminal = self._find_next_terminal(string)
            except ValueError:
                errors.append(f'Unexpected symbol {string[position]} at position {position}')
                position+=1
                continue
            stack_element = stack.pop()
            if stack_element.isNonTerminal:
                new_rule=self.syntax_analysis_table[stack_element].get(next_terminal)
                # TODO STOPPED HERE
            else:
                if stack_element == str_el:
                    position += 1
                else:
                    '''PANICCCCC'''
                    errors.append(f'Unexpected character {str_el} at position {position}')
                    position += 1
        return errors

    def _find_next_terminal(self, string:str)->Token:
        for terminal in sorted(list(self.terminals), key=lambda token: len(token.text), reverse=True):
            if string.startswith(terminal.text):
                return terminal
        raise ValueError('Unexpected terminal')