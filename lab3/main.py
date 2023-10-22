import os
import re
from PDA import PushdownAutomata
import logging

logging.basicConfig(level=logging.INFO)


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    @staticmethod
    def print(text: str, color: str):
        print(color + text + bcolors.ENDC)


def main():
    files = sorted([i for i in os.listdir() if re.match(".*.txt$", i) and i != "requirements.txt"])
    print("Choose file to process")
    for n, filename in enumerate(files):
        print(f"{n}. {filename}")
    filename = ""
    while not filename:
        try:
            inp = int(input())
            filename = files[inp]
        except Exception:
            print("Incorrect input")
    pda = PushdownAutomata.from_file(filename)
    if pda.is_determined:
        bcolors.print(f"PDA is determined", bcolors.OKGREEN)
    else:
        bcolors.print("PDA is not determined", bcolors.WARNING)
    if pda.string_to_process:
        res = pda.process_string()
        print(
            f"Processing string {pda.string_to_process}. Result is {bcolors.OKGREEN if res else bcolors.FAIL}{res}{bcolors.ENDC}")
        if res:
            print(f"Path: {'->'.join(pda.path)}")
    while True:
        result = pda.process_string(input("String to process: "))
        bcolors.print(str(result), bcolors.OKGREEN if result else bcolors.FAIL)
        if result:
            print(f"Path {';'.join(pda.path)}")


if __name__ == '__main__':
    main()
