import enum
import re


class Operation(enum.Enum):
    SUBTRACTION = '-'
    DIVISION = '/'
    ADDITION = '+'
    MULTIPLY = '*'
    POW = '^'
    NONE = ''
    NEGATIVE = None


class Expression:
    child_expressions: dict[str, str]
    expression: str
    operation: Operation | None

    def __init__(self, expr: str) -> None:
        expr=expr.replace(' ', '')
        expr=expr.replace('pow','')
        expr=expr.replace(',',')^(')
        expr=re.sub(r'^(-[0-9]+(?:\.[0-9]+)?)', '(\\1)', expr)
        self.check_operands_validity(expr)
        if expr.startswith('(') and expr.endswith(')'):
            br_stack=['(']
            for i in range(1,len(expr)):
                if expr[i]=='(':
                    br_stack.append('(')
                elif expr[i]==')':
                    br_stack.pop()
                if not br_stack and i!=len(expr)-1:
                    break
            else:
                expr = expr[1:-1]
        self.operation = None
        self.expression = expr
        self.child_expressions = {}
    
    def check_operands_validity(self, expr:str):
        if 'n' in expr:
            raise Exception('Wrong input symbol \'n\' is not allowed ')
        raw_expr=expr.replace('(-','n').replace('(','').replace(')','')
        operands=[raw_expr]
        for operation in Operation:
            if operation == Operation.NEGATIVE or operation == Operation.NONE:
                continue
            new_operands=[]
            for operand in operands:
                new_operands+=operand.split(operation.value)
            operands=new_operands
        print(f'{operands=}')
        for operand in operands:
            if not operand:
                raise Exception('No operand found for operation')
            if not re.match(r'^n*[0-9]+(?:\.[0-9]+)?$', operand):
                raise Exception(f'Unsupported operand {operand}')
    

    def iterate_over_operations(self, regex):
        while re.search(regex, self.expression):
            print(f'Iterator got string {self.expression}')
            yield re.search(regex, self.expression).groups()
            print("passed")
        print(f"exited with {self.expression}")

    def parse_expression(self):
        print(f"Parsing {self.expression=}")
        if self.expression.isdigit() or re.match(r'^[0-9]+\.[0-9]+$', self.expression):
            self.operation = Operation.NONE
            regex=r'^[0-9]+\.[0-9]+$'
            print(f"Set operation to NONE for {self.expression} [{self.expression.isdigit()=}, {re.match(regex, self.expression)}]")
            return
        
        brackets_stack = []
        current_bracket = ''
        expression_copy = self.expression
        for char in self.expression:
            if char == '(':
                brackets_stack.append('(')
            elif char == ')':
                try:
                    brackets_stack.pop()
                except IndexError:
                    raise IndexError("Wrong brackets")
                if not brackets_stack:
                    current_bracket += char
                    code = chr(ord('A') + len(self.child_expressions))
                    expression_copy = expression_copy.replace(current_bracket, code)
                    self.child_expressions[code] = current_bracket
                    current_bracket = ''
            if brackets_stack:
                current_bracket += char
        print(expression_copy, self.child_expressions)
        if brackets_stack:
            raise IndexError("Wrong brackets")
        self.expression = expression_copy
        print(f"checking if unMinus {self.expression=}")
        if re.match(r'^-[0-9]+(?:\.[0-9]+)?|-[A-Z]', self.expression):
            self.operation = Operation.NEGATIVE
            self.expression = self.expression[1:]
            return

    def calculate_expression(self) -> float:
        print(f"calculating expression {self.expression} {self.operation} {self.child_expressions}")
        if self.operation is not None:
            if self.operation == Operation.NONE:
                return float(self.expression)
            if self.operation == Operation.NEGATIVE:
                if self.expression.isalpha():
                    calc=Expression(self.child_expressions[self.expression])
                    calc.parse_expression()
                    self.expression=calc.calculate_expression()
                if not re.match("^([0-9]+(?:\.[0-9]+)?)$", self.expression):
                    calc=Expression(self.expression)
                    calc.parse_expression()
                    self.expression=calc.calculate_expression()
                return 0 - float(self.expression)
        print("CALCULATING POW")
        for op1, op2 in self.iterate_over_operations(
                r'([0-9]+\.[0-9]+|[0-9]|[A-Z])\^([0-9]+\.[0-9]+|[0-9]+|[A-Z])'):
            op1,op2=self.decode_values(op1, op2)
            self.insert_value(op1, '^', op2)
        print("CALCULATING */")
        for op1, operator, op2 in self.iterate_over_operations(
                r'([0-9]+\.[0-9]+|[0-9]|[A-Z])([*/])([0-9]+\.[0-9]+|[0-9]+|[A-Z])'):
            op1, op2 = self.decode_values(op1, op2)
            self.insert_value(op1, operator, op2)
        print("CALCULATING +-")
        for op1, operator, op2 in self.iterate_over_operations(
                r'([0-9]+\.[0-9]+|[0-9]|[A-Z])([-+])([0-9]+\.[0-9]+|[0-9]|[A-Z])'):
            op1, op2 = self.decode_values(op1, op2)
            self.insert_value(op1, operator, op2)
        try:
            return self.decode_values(self.expression)[0]
        except ValueError:
            raise Exception('Unsupported character')

    def insert_value(self, op1: float, operator: str, op2: float):
        if operator == Operation.ADDITION.value:
            res = op1 + op2
        elif operator == Operation.SUBTRACTION.value:
            res = op1 - op2
        elif operator == Operation.MULTIPLY.value:
            res = op1 * op2
        elif operator == Operation.DIVISION.value:
            res = op1 / op2
        elif operator == Operation.POW.value:
            res = op1 ** op2
            if type(res) is complex:
                raise Exception("Complex numbers are not supported")
        else:
            raise Exception(f'Unsupported operation {operator}')
        if res < 0:
            code = chr(len(self.child_expressions) + ord('A'))
            self.child_expressions[code] = f'({res})'
            self.expression = re.sub('([0-9]+\\.[0-9]+|[0-9]+|[A-Z])\\' + operator + '([0-9]+\\.[0-9]+|[0-9]+|[A-Z])',
                                     code,
                                     self.expression, count=1)
        else:
            self.expression = re.sub('([0-9]+\\.[0-9]+|[0-9]+|[A-Z])\\' + operator + '([0-9]+\\.[0-9]+|[0-9]+|[A-Z])',
                                     str(res),
                                     self.expression, count=1)

    def decode_values(self, *args):
        result = []
        for value in args:
            if value.isalpha():
                exp = Expression(self.child_expressions[value])
                exp.parse_expression()
                result.append(exp.calculate_expression())
            else:
                result.append(float(value))
        return result


def main():
    inp=input('Expression: ')
    expr = Expression(inp)
    # expr = Expression('2*(2+1)')
    expr.parse_expression()
    print("Result",expr.calculate_expression())
    print(f"actual {eval(inp)}")


if __name__ == '__main__':
    while True:
        main()
