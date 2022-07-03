##tokens that break down the user code
from asyncio import start_server
from distutils.log import error
from telnetlib import LINEMODE

#data type tokens
TOKEN_INT = 'INT'
TOKEN_FLOAT = 'FLOAT'

#Symbol tokens
TOKEN_OPENBRAC = 'OPENBRAC'
TOKEN_CLOSEBRAC = 'CLOSEBRAC'

#Operation tokens
TOKEN_MULIT = 'MULTI'
TOKEN_DIVIDE = 'DIVIDE'
TOKEN_PLUS = 'PLUS'
TOKEN_MINUS = 'MINUS'


TOKEN_EOF = 'EOF'

#Numbers
DIGITS = '1234567890'

#loops and key words
TOKEN_FLOOP = 'F_R'
TOKEN_WLOOP = 'WH_L_'
TOKEN_FUNC = 'F_NCT__N'
TOKEN_MINUS = 'MINUS'


class Token:
    def __init__(self, _type, val = None, startPos=None, endPos=None):
        self.type = _type
        self.value = val
        if startPos:
            self.startPos = startPos.copy()
            self.endPos = startPos.copy()
            self.endPos.adv()

        if endPos:
            self.endPos = endPos.copy()


    def __repr__(self):
        if self.value:return f'{self.type}:{self.value}'
        return f'{self.type}' 

class Position:
    def __init__(self, index, line, column, file_name, file_text):
        self.index = index
        self.line = line
        self.column = column
        self.file_name = file_name
        self.file_text = file_text

    def adv(self, current_char = None):
        self.index+=1
        if current_char == "\n":
            self.line+=1
            self.column = 0
    def copy(self):
        return Position(self.index, self.line, self.column, self.file_name, self.file_text)
#errors
class Error:
    def __init__(self, start, end,error_name, details):
        self.error_name = error_name
        self.details =details
        self.start =start
        self.end = end 

    def as_string(self):
        result = f'{self.error_name}: {self.details}\n'
        result+=  f'File {self.start.file_name}, Line {self.start.line+1}'
        return result

class IllegalCharError(Error):
    def __init__(self,start, end, details):
        super().__init__(start, end, "Illegal Character", details)

class IllegalSyntaxError(Error):
    def __init__(self,start, end, details):
        super().__init__(start, end, "Illegal Syntax", details)

class RuntimeError(Error):
    def __init__(self,start, end, details, context):
        super().__init__(start, end, "Runtime Error", details)
        self.context = context
    
    def as_string(self):
        result = self.generate_traceback()
        result = f'{self.error_name}: {self.details}\n'
        return result
    
    def generate_traceback(self):
        result = ''
        pos = self.start
        context = self.context

        while context:
            result =  f'File {"index.py"}, in {context.display_name}\n'+result
            pos = context.parent_entry_pos
            context = context.parent
        
        return 'Traceback (most recent call last): \n'+result
#Lexer
class Lex:
    def __init__(self,file_name, text):
        self.file_name = file_name
        self.text = text
        self.pos = Position(-1, 0, -1, file_name, text)
        self.current_char = None
        self.adv()

    def adv(self):
        self.pos.adv(self.current_char)
        self.current_char = self.text[self.pos.index] if self.pos.index<len(self.text) else None

    def generate_tokens(self):
        tokens = []

        while self.current_char!=None:
            if self.current_char in "\t":
                self.adv()
            elif self.current_char in DIGITS:
                tokens.append(self.trackNum())
            elif self.current_char == "+":
                tokens.append(Token(TOKEN_PLUS, startPos = self.pos))
                self.adv()
            elif self.current_char == "-":
                tokens.append(Token(TOKEN_MINUS, startPos = self.pos))
                self.adv()
            elif self.current_char == "*":
                tokens.append(Token(TOKEN_MULIT, startPos = self.pos))
                self.adv()
            elif self.current_char == "/":
                tokens.append(Token(TOKEN_DIVIDE, startPos = self.pos))
                self.adv()
            elif self.current_char == "(":
                tokens.append(Token(TOKEN_OPENBRAC, startPos = self.pos))
                self.adv()
            elif self.current_char == ")":
                tokens.append(Token(TOKEN_CLOSEBRAC, startPos = self.pos))
                self.adv()
            elif self.current_char == " ":
                self.adv()
            else:
                char =self.current_char
                start_pos = self.pos.copy()
                self.adv()
                return [], IllegalCharError(start_pos, self.pos, "'"+char+"'")
        tokens.append(Token(TOKEN_EOF, startPos = self.pos))
        return tokens, None


    def trackNum(self):
        numString = ''
        dotCount = 0
        startPos = self.pos.copy()
        while self.current_char != None and self.current_char in DIGITS +'.':
            if self.current_char == '.':
                if dotCount == 1: break
                dotCount+=1
                numString+='.'
            else:
                numString+=self.current_char
            self.adv()
        if dotCount == 0:
            return Token(TOKEN_INT, int(numString), startPos, self.pos )
        else:
            return Token(TOKEN_FLOAT,float(numString),  startPos, self.pos)

class numNode:
    def __init__(self, tok):
        self.tok=tok
        self.startPos = self.tok.startPos
        self.endPos = self.tok.endPos
        
    def __repr__(self):
        return f'{self.tok}'

class binaryOpNode:
    def __init__(self, lNode, op_tok, rNode) -> None:
        self.lNode = lNode
        self.op_tok = op_tok
        self.rNode = rNode

        self.startPos = self.lNode.startPos
        self.endPos = self.rNode.endPos

    def __repr__(self):
        return f'({self.lNode},{self.op_tok},{self.rNode})'


class unaryOpNode:
    def __init__(self, op_tok, node):
        self.op_tok = op_tok
        self.node = node
        self.startPos = self.op_tok.startPos
        self.endPos = node.endPos
    
    def __repr__(self):
        return f'({self.op_tok},{self.node})'

class ParseResult:
    def __init__(self):
        self.error = None
        self.node = None
    
    def reg(self, res):
        if isinstance(res, ParseResult):
            if res.error: self.error = res.error
            return res.node
        return res

    def success(self, node):
        self.node = node
        return self

    def failed(self, error):
        self.error = error
        return self




#parser
class Parser:
    def __init__(self,tokens):
        self.tokens = tokens
        self.tok_index = -1
        self.adv()

    def adv(self):
        self.tok_index+=1
        if self.tok_index <len(self.tokens):
            self.current_tok = self.tokens[self.tok_index]
        return self.current_tok


    def parse(self):
        res = self.expression()
        if not res.error and self.current_tok.type != TOKEN_EOF:
            return res.failed(IllegalSyntaxError(self.current_tok.startPos,self.current_tok.endPos," Expected operator + - / * "))
        return res

    def factor(self):
        tok = self.current_tok
        res = ParseResult()

        if tok.type in (TOKEN_MINUS, TOKEN_PLUS):
            res.reg(self.adv())
            factor = res.reg(self.factor())
            if res.error: return res
            return res.success(unaryOpNode(tok, factor))

        elif tok.type in (TOKEN_INT, TOKEN_FLOAT):
            res.reg(self.adv())
            return res.success(numNode(tok))
        
        elif tok.type == TOKEN_OPENBRAC:
            res.reg(self.adv())
            expr = res.reg(self.expression())
            if res.error: return res
            if self.current_tok.type == TOKEN_CLOSEBRAC:
                res.reg(self.adv())
                return res.success(expr)
            else:
                return res.failed(IllegalSyntaxError(self.current_tok.startPos,self.current_tok.endPos," Expected ')' "))

            
        #error here
        return res.failed(IllegalSyntaxError(tok.startPos, self.current_tok.endPos, " Expected INT or FLOAT "))
        
    def term(self):
        return self.binary_op(self.factor, (TOKEN_MULIT, TOKEN_DIVIDE))

    def expression(self):
        return self.binary_op(self.term, (TOKEN_MINUS, TOKEN_PLUS))



    def binary_op(self, func, ops):
        res = ParseResult()
        left = res.reg(func())
        if res.error: return res

        while self.current_tok.type in ops:
            op_tok = self.current_tok
            res.reg(self.adv())
            right = res.reg(func())
            if res.error:return res
            left = binaryOpNode(left, op_tok, right)

        return res.success(left)



class RuntimeRes:
    def __init__(self):
        self.value = None
        self.error = None
    def reg(self, res):
        if res.error: self.error = res.error
        return res.value
    def success(self, value):
        self.value = value
        return self
    def failed(self, error):
        self.error = error
        return self

class Number:
    def __init__(self, value):
        self.value = value
        self.set_position()
        self.set_context()
    
    def set_position(self, startPos = None, endPos = None):
        self.startPos = startPos
        self.endPos = endPos
        return self

    def set_context(self, context = None):
        self.context = context
        return self

    def add_to(self, other):
        if isinstance(other, Number):
            return Number(self.value+other.value).set_context(self.context), None

    def sub_by(self, other):
        if isinstance(other, Number):
            return Number(self.value-other.value).set_context(self.context),None
    def multi_by(self, other):
        if isinstance(other, Number):
            return Number(self.value*other.value).set_context(self.context),None
            
    def div_by(self, other):
        if isinstance(other, Number):
            if other.value == 0:
                return None, RuntimeError(other.startPos, other.endPos, " Division by 0 unsuccessful ", self.context)
            return Number(self.value/other.value).set_context(self.context), None

    def __repr__(self):
        return str(self.value)






class Context:
    def __init__(self, display_name, parent = None, parent_entry_pos = None):
        self.display_name = display_name
        self.parent = parent
        self.parent_entry_pos = parent_entry_pos








class Interpret:
    def visit(self, node, context):
        method_name = f'visit_{type(node).__name__}'
        method =getattr(self, method_name, self.no_visit_method)
        return method(node, context)
    
    def no_visit_method(self, node, context):
        raise Exception(f'No visit_{type(node).__name__} method defined')

    def visit_numNode(self, node, context):
        return RuntimeRes().success(Number(node.tok.value).set_context(context).set_position(node.startPos, node.endPos)) 

    def visit_binaryOpNode(self, node, context):
        res = RuntimeRes()
        l = res.reg(self.visit(node.lNode, context))
        if res.error: return res
        r = res.reg(self.visit(node.rNode, context))

        if node.op_tok.type == TOKEN_PLUS:
            result, error = l.add_to(r)
        elif node.op_tok.type == TOKEN_MINUS:
            result, error = l.sub_by(r)
        elif node.op_tok.type == TOKEN_MULIT:
            result, error = l.multi_by(r)
        elif node.op_tok.type == TOKEN_DIVIDE:
            result, error = l.div_by(r)
        if error:
            return res.failed(error)
        else:
            return res.success(result.set_position(node.startPos, node.endPos))

    def visit_unaryOpNode(self, node, context):
        res = RuntimeRes()
        number = res.reg(self.visit(node.node, context))
        if res.error: return res

        error = None
        if node.op_tok.type == TOKEN_MINUS:
            number, error = number.multi_by(Number(-1))

        if error:
            return res.failed(error)
        else:
            return res.success(number.set_position(node.startPos, node.endPos))

        



















def execute(fn, txt):
    lexer = Lex(fn,txt)
    tokens, error = lexer.generate_tokens()
    if error: return None, error

    parser = Parser(tokens)
    ast = parser.parse()
    if ast.error: return None, ast.error

    interpreter = Interpret()
    context = Context("<program>")
    result = interpreter.visit(ast.node, context)

    return result.value, result.error

