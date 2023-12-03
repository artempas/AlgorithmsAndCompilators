from dataclasses import dataclass, field
from logging import getLogger

logger = getLogger('Nonterminal')


def get_from_string(string: str, i: int) -> str | None:
    if len(string) - 1 < i:
        return None
    return string[i]


@dataclass(frozen=True)
class Token:
    isNonTerminal: bool
    text: str
    is_reversed: bool = False

    def __lt__(self, other: 'Token'):
        return self.text < other.text

    def test(self, string: str) -> bool:
        if self.isNonTerminal:
            return False
        return string != self.text if self.is_reversed else string == self.text


@dataclass
class Rule:
    rule: list[Token] = field(default_factory=list)
    sync: bool = False

    def __str__(self):
        return ('Sync' if self.sync else '') + ''.join([
            f"<{i.text}>" if i.isNonTerminal else f"'{i.text}'" for i in self.rule])

    def __iter__(self):
        for token in self.rule:
            yield token


class Nonterminal:

    def __init__(self, name: str, rules: list[str], is_first=False) -> None:
        self.is_first = is_first
        self.name = name
        self.rules = self._parse_rules(rules)
        logger.debug(f"Created Nonterminal {name}. Rules are: {self.rules}")

    def _parse_rules(self, rules: list[str]) -> list[Rule]:
        res_rules = []
        for rule in rules:
            current_rule = []
            is_processing_terminal = False
            is_processing_nonterminal = False
            is_ignore_rule = False
            current_token = ''
            for i, char in enumerate(rule):
                if not (is_processing_terminal or is_processing_nonterminal):
                    if char == '<':
                        is_processing_nonterminal = True
                        current_token = ''
                        continue
                    elif char == '\'':
                        is_processing_terminal = True
                        current_token = ''
                        continue
                    elif char == '@':
                        current_rule.append(Token(isNonTerminal=False, text='@'))
                    elif char == '!' and get_from_string(rule, i + 1) == "<":
                        is_ignore_rule = True
                    elif char != ' ':
                        raise ValueError(f'Unexpected token {char} in rule {rule} (Terminal {self.name})')
                    continue
                if is_processing_terminal:
                    if char == '\'':
                        is_processing_terminal = False
                        current_rule.append(Token(isNonTerminal=False, text=current_token))
                    else:
                        current_token += char
                        continue
                if is_processing_nonterminal:
                    if char == '>':
                        is_processing_nonterminal = False
                        current_rule.append(Token(isNonTerminal=True, text=current_token, is_reversed=is_ignore_rule))
                        is_ignore_rule = False
                    else:
                        current_token += char
            res_rules.append(Rule(rule=current_rule))
        return res_rules

    @staticmethod
    def first_for_rule(rule: Rule, other_nonterminals: dict[str, 'Nonterminal']) -> set[Token]:
        rule = rule.rule
        if not rule:
            return {Token(isNonTerminal=False, text='@')}
        result = set()
        for i, token in enumerate(rule):
            if token.isNonTerminal:
                other_first = other_nonterminals[token.text].first(other_nonterminals)
                if '@' not in other_first:
                    result = result.union(other_first)
                    break
                else:
                    if i == len(rule) - 1:  # If the last one returns @ have to add it to first.
                        result = result.union(other_first)
                        break
                    else:  # Else try next one
                        other_first.remove(Token(False, '@'))
                        result = result.union(other_first)
                        continue
            else:
                result.add(token)
                break
        return result

    def first(self, other_rules: dict[str, 'Nonterminal']) -> set[Token]:
        result = set()
        for rule in self.rules:
            result = result.union(self.first_for_rule(rule, other_rules))
        return result

    @property
    def token(self) -> Token:
        return Token(isNonTerminal=True, text=self.name)

    def follow(self, other_nonterminals: dict[str, 'Nonterminal'], ignore: 'Nonterminal' = None) -> set[Token]:
        follow = set()
        if self.is_first:
            follow.add(Token(isNonTerminal=False, text='$'))
        for nonterminal in other_nonterminals.values():
            for rule in nonterminal.rules:
                rule = rule.rule
                last_token_position = 0
                for _ in range(rule.count(self.token)):
                    last_token_position = rule.index(self.token, last_token_position) + 1
                    subrule = rule[last_token_position:]
                    first_of_subrule = self.first_for_rule(Rule(subrule), other_nonterminals)
                    if '@' not in [i.text for i in first_of_subrule]:
                        follow = follow.union(first_of_subrule)
                    else:
                        if self == nonterminal and first_of_subrule == {Token(False, "@")}:
                            continue
                        follow = follow.union(first_of_subrule)
                        if nonterminal != ignore:
                            follow = follow.union(nonterminal.follow(other_nonterminals, ignore=self))
        return follow

    def get_terminals(self) -> set[Token]:
        terminals = set()
        for rule in self.rules:
            for token in rule.rule:
                if not token.isNonTerminal:
                    terminals.add(token)
        return terminals
