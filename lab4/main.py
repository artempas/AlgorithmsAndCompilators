from Parser import Parser
import logging

def main():
    parser=Parser.from_file('/home/artempas/AlgorythmsAndCompilators/lab4/Cgrammar.txt')
    logging.basicConfig(level=logging.DEBUG)

if __name__=='__main__':
    main()
