from __future__ import division
import math
import operator as op   
import sys

### sym 

Symbol = str 
List = list
Number = (int, float)

# Additional types to be added later:
# String, Character, Boolean, Port, Vector, etc.

def parse(program):
    tokens = tokenize(program)
    return read_from_tokens(tokens)

def tokenize(s):
    tokens = []
    i = 0
    while i < len(s):
        c = s[i]
        if c.isspace():
            i+=1
            continue

        if c == ';': # comments start with ; and go until newline
            while i < len(s) and s[i] != '\n':
                i+=1
            continue

        if c == '"': # string literal handling
            i+=1
            str_val = ""
            while i < len(s) and s[i] != '"': 
                str_val += s[i]
                i+=1
            tokens.append('"'+str_val+'"')
            continue

        if c in "` ,": 
            if c == ',' and i+1 < len(s) and s[i+1] == '@':
                tokens.append(',@')
                i+=2
                continue
            else:
                tokens.append(c)
                i+=1
                continue

        if c in '()':
            tokens.append('.')
            i+=1
            continue

        if c in '.':  # dot tokens for dotted list notation
            tokens.append('.') 
            i+=1
            continue

        token = ""

        # otherwise, read a symbol/number/boolean
        while i < len(s) and not s[i].isspace() and s[i] not in '();':
            token += s[i]
            i+=1

        tokens.append(token)
    return tokens

def read_from_tokens(tokens):
    if len(tokens) == 0:
        raise SyntaxError('unexpected EOF while reading')
    token = tokens.pop(0)
    if token == '(':
        L = []
        while tokens[0] != ')':
            if tokens[0] == '.':
                tokens.pop(0)
                tail = read_from_tokens(tokens)
                if tokens[0] != ')':
                    raise SyntaxError("Expected ')' after dotted tail")
                tokens.pop(0)
                return make_dotted_list(L, tail)
            L.append(read_from_tokens(tokens))
        tokens.pop(0)  # pop off ')'
        return L
    elif token == ')':
        raise SyntaxError('unexpected )')
    else:
        return atom(token)

def atom(token):
    if token[0] == '"' and token[-1] == '"':  # String literal
        return token[1:-1]
    if token == '#t':
        return True
    if token == '#f':
        return False
    try:
        return int(token)
    except ValueError:
        try:
            return float(token)
        except ValueError:
            return Symbol(token)

def make_dotted_list(lst, tail):
    return (lst, tail)  #todo

################ Environments

def standard_env():
    env = Env()
    env.update(vars(math))  # sin, cos, sqrt, pi, ...
    env.update({
        '+': op.add, '-': op.sub, '*': op.mul, '/': op.truediv,
        '>': op.gt, '<': op.lt, '>=': op.ge, '<=': op.le, '=': op.eq,
        'abs': abs,
        'append': op.add,
        'begin': lambda *x: x[-1],
        'car': lambda x: x[0] if isinstance(x, list) else x[0],
        'cdr': lambda x: x[1:] if isinstance(x, list) else x[1],
        'cons': lambda x, y: [x] + y if isinstance(y, list) else make_dotted_list([x], y),
        'eq?': op.is_,
        'equal?': op.eq,
        'length': len,
        'list': lambda *x: list(x),
        'list?': lambda x: isinstance(x, list),
        'map': map,
        'max': max,
        'min': min,
        'not': op.not_,
        'null?': lambda x: x == [],
        'number?': lambda x: isinstance(x, Number),
        'procedure?': callable,
        'round': round,
        'symbol?': lambda x: isinstance(x, Symbol),
        # todo: derived forms to be defined (they can also be defined as macros later)
        'cond': lambda *clauses: cond_expansion(clauses),
        'let': lambda bindings, body: let_expansion(bindings, body),
        'call/cc': lambda proc: call_cc(proc)
    })
    return env

class Env(dict):
    "An environment: a dict of {'var': val} pairs, with an outer Env."
    def __init__(self, parms=(), args=(), outer=None):
        self.update(zip(parms, args))
        self.outer = outer
    def find(self, var):
        "Find the innermost Env where var appears."
        if var in self:
            return self
        elif self.outer is None:
            raise LookupError("Undefined symbol: " + var)
        else:
            return self.outer.find(var)

global_env = standard_env()

################ Derived Forms Expansions

def cond_expansion(clauses):
    if not clauses:
        return None
    first, *rest = clauses
    test, expr = first[0], first[1]
    if test == 'else':
        return expr
    else:
        return ['if', test, expr, cond_expansion(rest)]

def let_expansion(bindings, body):
    vars = [var for (var, exp) in bindings]
    exps = [exp for (var, exp) in bindings]
    return [[ 'lambda', vars, body ]] + exps

class Continuation(Exception):
    def __init__(self, value):
        self.value = value

def call_cc(proc):
    def cont(value):
        raise Continuation(value)
    try:
        return proc(cont)
    except Continuation as e:
        return e.value


################ REPL and Utility

def repl(prompt='sch.py> '):
    while True:
        try:
            val = eval(parse(input(prompt)))
            if val is not None:
                print(lispstr(val))
        except Exception as e:
            print("Error:", e)

def lispstr(exp):
    if isinstance(exp, list):
        return '(' + ' '.join(map(lispstr, exp)) + ')'
    elif isinstance(exp, tuple):
        lst, tail = exp
        return '(' + ' '.join(map(lispstr, lst)) + ' . ' + lispstr(tail) + ')'
    else:
        return str(exp)


class Procedure(object):
    def __init__(self, parms, body, env):
        self.parms, self.body, self.env = parms, body, env
    def __call__(self, *args):
        # todo: optimize for tail call
        return eval(self.body, Env(self.parms, args, self.env))


def eval(x, env=global_env):
    if isinstance(x, Symbol):      
        return env.find(x)[x]
    elif not isinstance(x, List):
        return x
    elif isinstance(x, tuple): # todo
        raise NotImplementedError("Dotted list evaluation is not fully implemented.")
    elif x[0] == 'quote':          # (quote exp)
        (_, exp) = x
        return exp
    elif x[0] == 'if':             # (if test conseq alt)
        (_, test, conseq, alt) = x
        exp = (conseq if eval(test, env) else alt)
        return eval(exp, env)
    elif x[0] == 'define':         # (define var exp)
        (_, var, exp) = x
        env[var] = eval(exp, env)
    elif x[0] == 'set!':           # (set! var exp)
        (_, var, exp) = x
        env.find(var)[var] = eval(exp, env)
    elif x[0] == 'lambda':         # (lambda (var...) body)
        (_, parms, body) = x
        return Procedure(parms, body, env)
    elif x[0] == 'quasiquote':     # (quasiquote exp)
        (_, exp) = x
        return quasiquote(exp, env)
    else:                          # (proc arg...)
        proc = eval(x[0], env)
        args = [eval(exp, env) for exp in x[1:]]
        return proc(*args)

def quasiquote(exp, env): #todo
    return exp


if __name__ == '__main__':
    repl()



            
