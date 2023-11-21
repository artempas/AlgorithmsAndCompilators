
from dataclasses import dataclass
from enum import Enum
from logging import getLogger

logger=getLogger('Nonterminal')


@dataclass    
class Token:
    isTerminal:bool
    text:str

class Nonterminal:    

    def __init__(self, name:str, rules:list[str]) -> None:
        print(rules)
        self.name=name
        self.rules=self._parse_rules(rules)
        print(f"Created Nonterminal {name}. Rules are: {self.rules}")
        
    
    def _parse_rules(self, rules:list[str])->list[list[Token]]:
        res_rules=[]
        for rule in rules:
            current_rule=[]
            is_processing_terminal=False
            is_processing_nonterminal=False
            current_token=None
            for char in rule:
                if not (is_processing_terminal or is_processing_nonterminal):
                    if char=='<':
                        is_processing_nonterminal=True
                        current_token=Token(isTerminal=True, text='')
                        continue
                    elif char=='\'':
                        is_processing_terminal=True
                        current_token=Token(isTerminal=False,text='')
                        continue
                    elif char!=' ':
                        raise ValueError(f'Unexpected token {char} in rule {rule} (Terminal {self.name})')
                    continue
                if is_processing_terminal:
                    if char=='\'':
                        is_processing_terminal=False
                        current_rule.append(current_token)
                    else:
                        current_token.text+=char
                        continue
                if is_processing_nonterminal:
                    if char=='>':
                        is_processing_terminal=False
                        current_rule.append(current_token)
                    else:
                        current_token.text+=char
            res_rules.append(current_rule)



