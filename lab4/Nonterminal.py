from dataclasses import dataclass
from enum import Enum
from logging import getLogger

logger = getLogger('Nonterminal')


@dataclass
class Token:
    isNonTerminal: bool
    text: str


class Nonterminal:

    def __init__(self, name: str, rules: list[str], is_first=False) -> None:
        self.is_first = is_first
        self.name = name
        self.rules = self._parse_rules(rules)
        print(f"Created Nonterminal {name}. Rules are: {self.rules}")

    def _parse_rules(self, rules: list[str]) -> list[list[Token]]:
        res_rules = []
        for rule in rules:
            current_rule = []
            is_processing_terminal = False
            is_processing_nonterminal = False
            current_token = None
            for char in rule:
                if not (is_processing_terminal or is_processing_nonterminal):
                    if char == '<':
                        is_processing_nonterminal = True
                        current_token = Token(isNonTerminal=True, text='')
                        continue
                    elif char == '\'':
                        is_processing_terminal = True
                        current_token = Token(isNonTerminal=False, text='')
                        continue
                    elif char != ' ':
                        raise ValueError(f'Unexpected token {char} in rule {rule} (Terminal {self.name})')
                    continue
                if is_processing_terminal:
                    if char == '\'':
                        is_processing_terminal = False
                        current_rule.append(current_token)
                    else:
                        current_token.text += char
                        continue
                if is_processing_nonterminal:
                    if char == '>':
                        is_processing_nonterminal = False
                        current_rule.append(current_token)
                    else:
                        current_token.text += char
            res_rules.append(current_rule)
        return res_rules

    @staticmethod
    def first_for_rule(rule: list[Token], other_rules: dict[str, 'Nonterminal']) -> set[str]:
        if not rule:
            return {'@'}
        result = set()
        for i, token in enumerate(rule):
            if token.isNonTerminal:
                other_first = other_rules[token.text].first(other_rules)
                if '@' not in other_first:
                    result = result.union(other_first)
                    break
                else:
                    if i == len(rule) - 1:  # If the last one returns @ have to add it to first.
                        result = result.union(other_first)
                        break
                    else:  # Else try next one
                        other_first.remove('@')
                        result = result.union(other_first)
                        continue
            else:
                result.add(token.text)
                break
        return result

    def first(self, other_rules: dict[str, 'Nonterminal']) -> set[str]:
        result = set()
        for rule in self.rules:
            result = result.union(self.first_for_rule(rule, other_rules))
        return result

    @property
    def token(self) -> Token:
        return Token(isNonTerminal=True, text=self.name)

    def follow(self, other_rules: dict[str, 'Nonterminal']) -> set[str]:
        follow = set()
        if self.is_first:
            follow.add('$')
        for nonterminal in other_rules.values():
            for rule in nonterminal.rules:
                try:
                    if self.name=='statement' and nonterminal.name=='else':
                        pass
                    token_position = rule.index(self.token)
                    subrule = rule[token_position + 1:]
                    first_of_subrule = self.first_for_rule(subrule, other_rules)
                    if '@' not in first_of_subrule:
                        follow = follow.union(first_of_subrule)
                    else:
                        if self==nonterminal and first_of_subrule=={"@"}:
                            continue
                        follow = follow.union(nonterminal.follow(other_rules))
                except ValueError:  # If current nonterminal wasn't found in rule
                    continue
        return follow
