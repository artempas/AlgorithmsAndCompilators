from lab5.ProcessorParser import ProcessorParser
from lab5.Instruction import INSTRUCTION_TYPES
from lab4.main import main as lab4

def main():
    parser = ProcessorParser()
    errors = lab4('./lab5/CGrammar.txt', './lab5/test1.txt', False)
    if errors:
        for i in errors:
            print(i)
    else:
        print("No syntax errors found")
        with open('./lab5/test1.txt', encoding='utf-8') as file:
            instructions = parser.process_program(file.read())
            variables = {}
            if_succeed = None
            for instruction in instructions:
                if instruction.type == INSTRUCTION_TYPES.ELSE_STATEMENT:
                    if if_succeed == False:
                        variables, if_succeed = instruction.execute(variables)
                    continue
                variables, if_succeed = instruction.execute(variables)

if __name__ == '__main__':
    main()
