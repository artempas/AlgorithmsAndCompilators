from lab5.Instruction import Instruction


class ProcessorParser():
    def process_program(self, string: str):
        processing_stack: list[Instruction] = []
        current_instruction: str = ''
        result: list[Instruction] = []
        for char in string:
            match char:
                case '{':
                    processing_stack.append(Instruction(current_instruction))
                    current_instruction = ''
                case '}':
                    complete_instruction = processing_stack.pop()
                    if processing_stack:
                        processing_stack[-1].body.append(complete_instruction)
                    else:
                        result.append(complete_instruction)
                case ';':
                    if processing_stack:
                        processing_stack[-1].body.append(Instruction(current_instruction))
                    else:
                        result.append(Instruction(current_instruction))
                    current_instruction = ''
                case '\n':
                    continue
                case _:
                    current_instruction += char
        return result
