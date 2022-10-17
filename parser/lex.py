import ply.lex as lex
import sys
import os

tokens = [
    'START',
    'EPS',
    'EQ',
    'NON_TERMINAL',
    'SYMBOL',
    'PLUS',
    'ALT',
    'LBR',
    'RBR',
    'LSB',
    'RSB',
    'LFB',
    'RFB',
    'END_OF_LINE',
    'COMMENT'
]


def clean_terminal(token_val: lex.LexToken) -> lex.LexToken:
    token_val = token_val.replace("\\\"", "\"")
    token_val = token_val.replace("\\#", "#")
    token_val = token_val.replace("\\\\", "\\")
    return token_val


def t_NON_TERMINAL(t: lex.LexToken) -> lex.LexToken:
    r'[A-Za-z][A-Za-z_0-9]*'

    match t.value:
        case "START":
            t.type = "START"
        case "EPS":
            t.type = "EPS"
        case _:
            t.type = "NON_TERMINAL"
    return t


def t_SYMBOL(t: lex.LexToken) -> lex.LexToken:
    r'\"(?:[^\\\"\#]|\\.)*\"'

    t.value = clean_terminal(t.value[1:-1])
    t.type = "SYMBOL"
    return t


def t_COMMENT(t: lex.LexToken) -> lex.LexToken:
    r'\#.*$'

    t.value = t.value[1:]
    return t


def t_newline(t: lex.LexToken):
    r'\n+'

    t.lexer.lineno += len(t.value)


def t_error(t: lex.LexToken):
    print("Error: invalid character: \'{}\'".format(t.value[0]))
    t.lexer.skip(1)


t_EQ = '='
t_PLUS = '\+'
t_ALT = '\|'
t_LBR = '\('
t_RBR = '\)'
t_LSB = '\['
t_RSB = '\]'
t_LFB = '\{'
t_RFB = '\}'
t_END_OF_LINE = '\;'
t_ignore = ' \t'

lexer = lex.lex()


def main():
    if len(sys.argv) < 2:
        print("Lexer must get at least 1 filename to work with")

    for filename_input in sys.argv[1:]:
        with open(filename_input, "r") as filein, open('.'.join(os.path.splitext(filename_input)[:-1]) + ".lexout",
                                                       "w") as file_output:

            print("EBNF: performing lexical analysis for file "
                  "\"{}\" to file \"{}\"...".format(filename_input, file_output.name))
            for lexer_input_data in filein.readlines():
                lexer.input(lexer_input_data)
                while True:
                    token = lexer.token()
                    if not token:
                        break
                    print(token, file=file_output)


if __name__ == "__main__":
    main()
