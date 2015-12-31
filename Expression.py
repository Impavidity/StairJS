from NonTerminal import *
from Object import *
import Engine
from Control import statement_list


def primary_expression(ast, context):
    pe = ast[1]
    if isinstance(pe, list):
        return Engine.engine[pe[0]](pe, context)
    else:
        return context.this


def identifier(ast, context):
    def find_out(ctxt, iden):
        if iden in ctxt.outFunction:
            return ctxt.outFunction[iden]
        elif ctxt.outFunction is not Engine.glb:
            return find_out(ctxt.outFunction, iden)

    if ast[1] in context:
        return context[ast[1]]
    elif ast[1] in context.this.obj:
        return context.this.obj[ast[1]]
    else:
        return find_out(context, ast[1])


def array_literal(ast, context):
    obj = StObject()
    element_list(ast[2], context, obj)
    return obj


def element_list(ast, context, obj):
    i = 0
    for child in ast:
        if isinstance(child, list) and child[0] == AssignmentExpressionNoIn:
            obj[i] = StRef(assignment_expression_no_in(child, context))
        elif child == ',':
            i += 1


def element_list_end_with_ex(ast, context):
    Engine.traverse(ast, context)


def object_literal(ast, context):
    obj = StObject()
    if len(ast) == 4:
        property_name_and_value_list(ast[2], context, obj)
    return obj


def property_name_and_value_list(ast, context, obj):
    for child in ast:
        if isinstance(child, list) and child[0] == PropertyNameAndValue:
            property_name_and_value(child, context, obj)


def property_name_and_value(ast, context, obj):
    obj[property_name(ast[1], context)] = StRef(assignment_expression_no_in(ast[3], context))


def property_name(ast, context):
    if isinstance(ast[1], list):
        return ast[1][1]
    else:
        return ast[1]


def member_expression(ast, context):
    mem = Engine.engine[ast[1][0]](ast[1], context)
    if len(ast) == 3:
        mem_part = member_expression_part(ast[2], context)
        if mem_part in mem.obj:
            return mem.obj[mem_part], mem
        else:
            mem.obj[mem_part] = UNDEFINED
            return mem.obj[mem_part], mem
    return mem


def allocation_expression(ast, context):
    obj = StObject()
    new_ar = StActiveRecord()
    func_proto = member_expression(ast[2], context)
    new_ar.this = StRef(obj)
    if isinstance(func_proto, tuple):
        func_proto = func_proto[0]
    new_ar.outFunction = context.outFunction

    arguments_list = arguments(ast[3], context)
    new_ar["arugments"] = arguments_list

    code = func_proto.obj.ast
    formal_list = func_proto.obj.argument_list
    for i in range(0, len(formal_list)):
        if i in arguments_list:
            new_ar[formal_list[i]] = arguments_list[i]
        else:
            new_ar[formal_list[i]] = Undefined()
    func_body = None
    for x in code:
        if isinstance(x, list) and x[0] == FunctionBody:
            func_body = x
            break
    function_body(func_body, new_ar)
    return obj


def member_expression_part(ast, context):
    if ast[2][0] == ExpressionNoIn:
        return expression_no_in(ast[2], context)
    elif ast[2][0] == Identifier:
        return ast[2][1]


def call_expression(ast, context):
    new_ar = StActiveRecord()
    member = Engine.engine[ast[1][0]](ast[1], context)  # resolve member
    if isinstance(member, tuple):
        new_ar.this = member[1]  # object context
        new_ar.outFunction = context.outFunction
        func_proto = member[0]
    else:
        func_proto = member
        new_ar.this = context.this
        new_ar.outFunction = context.outFunction
    arguments_list = arguments(ast[2], context)

    new_ar["arugments"] = arguments_list

    code = func_proto.obj.ast
    formal_list = func_proto.obj.argument_list
    for i in range(0, len(formal_list)):
        if i in arguments_list:
            new_ar[formal_list[i]] = arguments_list[i]
        else:
            new_ar[formal_list[i]] = Undefined()
    func_body = None
    for x in code:
        if isinstance(x, list) and x[0] == FunctionBody:
            func_body = x
            break
    return function_body(func_body, new_ar)


def call_expression_part(ast, context):
    Engine.traverse(ast, context)


def arguments(ast, context):
    if len(ast) == 3:
        return {}
    else:
        return argument_list(ast[2], context)


def argument_list(ast, context):
    ret = {}
    i = 0
    for x, y in Engine.iterate(ast, context):
        ret[i] = x
        i += 1
    return ret


def right_hand_side_expression(ast, context):
    if ast[1][0] == CallExpression:
        return call_expression(ast[1], context)
    elif ast[1][0] == MemberExpression:
        ret = member_expression(ast[1], context)
        if isinstance(ret, tuple):
            return ret[0]
        else:
            return ret


def left_hand_side_expression(ast, context):
    if ast[1][0] == Identifier:
        return identifier(ast[1], context)
    elif ast[1][0] == CallExpression:
        mem = call_expression(ast[1], context)
        mem_part = member_expression_part(ast[2], context)
        if not (mem_part in mem):
            mem[mem_part] == StRef(UNDEFINED)
        return mem[mem_part]
    elif ast[1][0] == MemberExpression:
        mem = member_expression(ast[1], context)
        mem_part = member_expression_part(ast[2], context)
        if not (mem_part in mem.obj):
            mem.obj[mem_part] = StRef(UNDEFINED)
        return mem.obj[mem_part]


def assignment_expression_no_in(ast, context):
    if len(ast) > 2:
        left = Engine.engine[ast[1][0]](ast[1], context)
        right = Engine.engine[ast[3][0]](ast[3], context)
        if isinstance(right, StRef):
            left.obj = right.obj
        else:
            left.obj = right
        return left.obj
    else:
        return Engine.engine[ast[1][0]](ast[1], context)


def assignment_operator(ast, context):
    Engine.traverse(ast, context)


def expression_no_in(ast, context):
    return assignment_expression_no_in(ast[1], context)


def function_declaration(ast, context):
    Engine.traverse(ast, context)


def function_expression(ast, context):
    func_proto = StFunction()
    func_proto.ast = ast
    for fpl in ast:
        if isinstance(fpl, list) and fpl[0] == Identifier:
            context[fpl[1]] = func_proto
        if isinstance(fpl, list) and fpl[0] == FormalParameterList:
            func_proto.argument_list = formal_parameter_list(fpl, context)
    return func_proto


def formal_parameter_list(ast, context):
    ret = []
    for x in ast:
        if isinstance(x, list):
            ret.append(x[1])
    return ret


def more_formal_parameter(ast, context):
    Engine.traverse(ast, context)


def function_body(ast, context):
    ret = statement_list(ast[2], context)
    return context.return_value


def variable_statement(ast, context):
    var = ast[2][1]
    if len(ast) <= 4:
        context[var] = StRef(UNDEFINED)
    else:
        context[var] = StRef(assignment_expression_no_in(ast[4], context))
