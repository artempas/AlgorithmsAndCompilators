import typing
from logging import getLogger
from prettytable import PrettyTable

from Nonterminal import Nonterminal, Token, Rule
import re

logger = getLogger('Parser')


class Stack(list):
    def append(self, __object: '_T') -> None:
        logger.debug(f"stack {self}<-{__object}")
        super().append(__object)

    def pop(self, __index: typing.SupportsIndex = ...) -> '_T':
        obj = super().pop()
        logger.debug(f"stack {self}->{obj}")
        return obj


class Parser:
    nonterminals: dict[str, Nonterminal]
    NT_RULE = r"<(?P<nonterminal>[a-z_]+)>: *(?P<rules>.*)?"
    NT_OR_RULE = r"\t\| (?P<rules>.+)"
    parsing_table: dict[Token, dict[Token, Rule]]
    syntax_analysis_table: dict[Token, dict[Token, Rule]]

    class Error(typing.NamedTuple):
        message: str
        position: int
        skipped: bool

    def __init__(self) -> None:
        self.syntax_analysis_table = {}
        self.parsing_table = {}
        self.nonterminals = {}

    @classmethod
    def from_file(cls, filename):
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
            rules = rule_str.split('|') if rule_str else ['@']
            return found.group('nonterminal'), rules
        found = re.match(self.NT_OR_RULE, string)
        if found:
            return None, found.group('rules').split('|')
        raise ValueError(f'cannot parse string {string}')

    def __build_parsing_table(self) -> None:
        table: dict[Token, dict[Token, Rule]] = {}  # [nonterminal][terminal]
        for nonterminal in self.nonterminals.values():
            table[nonterminal.token] = {}
            for rule in nonterminal.rules:
                first = Nonterminal.first_for_rule(rule, self.nonterminals)
                if '@' not in [i.text for i in first]:
                    for terminal in first:
                        table[nonterminal.token][terminal] = rule
                else:
                    for terminal in first:
                        if terminal.text != '@':
                            table[nonterminal.token][terminal] = rule
                    for terminal in nonterminal.follow(self.nonterminals):
                        logger.debug(f'table[{nonterminal.token.text}][{terminal.text}]={rule}')
                        table[nonterminal.token][terminal] = rule

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
                current_rule = self.syntax_analysis_table[nonterminal.token].get(terminal)
                if current_rule:
                    self.syntax_analysis_table[nonterminal.token][terminal].sync = True
                else:
                    self.syntax_analysis_table[nonterminal.token][terminal] = Rule(sync=True)
            for terminal in nonterminal.first(self.nonterminals):
                if terminal.text=='@':
                    continue
                self.syntax_analysis_table[nonterminal.token][terminal].sync = True

    def test_string(self, string: str) -> list[Error]:
        """
        Parses string, returns errors
        """

        stack = Stack([Token(False, '$'), Token(True, 'program')])
        errors = []
        position = 0
        in_panic = False

        def panic_mode():
            nonlocal position, in_panic
            while position <= len(string) and in_panic:
                errors.append(self.Error('', position, True))
                while string[position] in (' ', '\n') and position < len(string):
                    position += 1
                next_terminal = self._find_next_terminal(string[position:])
                new_rule = self.syntax_analysis_table[stack_element].get(next_terminal)
                if new_rule:
                    if new_rule.sync:
                        position += 1
                        in_panic = False
                position += 1

        while position < len(string):
            next_terminal = None
            try:
                while string[position] in (' ', '\n') and position < len(string)-1:
                    position += 1
                next_terminal = self._find_next_terminal(string[position:])
            except ValueError:
                errors.append(self.Error('Not found terminal', position, False))
                position += 1
                continue
            stack_element = stack.pop()
            if stack_element.isNonTerminal:
                new_rule = self.syntax_analysis_table[stack_element].get(next_terminal)
                if new_rule:
                    if new_rule.rule:
                        for token in new_rule.rule[::-1]:
                            stack.append(token)
                        continue
                    else:
                        assert new_rule.sync
                        errors.append(
                            self.Error(f'Next rule not found for {stack_element.text}[{next_terminal.text}] (synch)',
                                       position, False))
                        stack.pop()
                        position += 1
                        continue
                else:
                    in_panic = True
                    errors.append(
                        self.Error(f'Next rule not found for {stack_element.text}[{next_terminal.text}]', position,
                                   False))
                    position += 1
                    panic_mode()
                    continue
            else:
                if stack_element == next_terminal:
                    position += len(next_terminal.text)
                elif stack_element==Token(False, "@"):
                    continue
                else:
                    '''PANICCCCC'''
                    errors.append(
                        self.Error(f'Unexpected symbol (expected {stack_element.text} got {string[position]})', position,
                                   False))
                    in_panic = True
                    position += 1
                    while not stack_element.isNonTerminal:
                        if not stack:
                            errors += [self.Error('', i, True) for i in range(position, len(string))]
                            return errors
                        stack_element = stack.pop()
                    panic_mode()
                    continue
        errors+=[self.Error(f"Expected {i.text}" , -1, False) for i in stack[1:][::-1]]
        return errors

    def _find_next_terminal(self, string: str) -> Token:
        for terminal in sorted(list(self.terminals), key=lambda token: len(token.text), reverse=True):
            if string.startswith(terminal.text):
                return terminal
        raise ValueError(f'Unable to find next terminal in {string.__repr__()}')
