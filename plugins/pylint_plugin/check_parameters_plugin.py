import astroid
import json
from pylint import checkers, interfaces

print(f"Astroid version: {astroid.__version__}")

with open("numpy_verified_removed_objects.json", 'r') as f:
    obj = json.load(f)

def get_parameter_keys():
    PARAM_KEYS = []
    for p in obj:
        if 'Parameter' in p:
            PARAM_KEYS.append(p)
    print(f'Loaded {len(PARAM_KEYS)}')
    return PARAM_KEYS

p_keys = get_parameter_keys()

print("I will be parsing through the keys listed:")

TARGETS_TO_FIND = {}
PARAMS_TO_FIND = {}

for k in p_keys:
    print(k)
    TARGETS_TO_FIND.update({k: [i[0] for i in obj[k]]})
    PARAMS_TO_FIND.update({k: [i[1] for i in obj[k]]})

class ParameterRemovedChecker(checkers.BaseChecker):
    schemaKey = 'ParameterRemoved'
    FUNCTIONS_TO_FIND = [i.split('.')[-1] for i in TARGETS_TO_FIND[schemaKey]]
    PARAMS = PARAMS_TO_FIND[schemaKey]

    __implements__ = (interfaces.IAstroidChecker,)

    name = 'removed-parameters-checker'
    priority = -1
    msgs = {
        'W0010': (
            'Found use of %s in func %s',
            'proposed-removed-parameters',
            'This parameter has been removed in an upcoming version of this package.',
        ),
    }

    def visit_call(self, node):
        func = node.func
        if not isinstance(func, astroid.Attribute) or (func.attrname not in FUNCTIONS_TO_FIND):
            return
        try:
            inferred_values = list(func.expr.infer())
            for inferred in inferred_values:
                if inferred is astroid.Uninferable:
                    print(f"Uninferable error: inferred {inferred} in {inferred_values}, with {func.attrname}")
                    continue
                function_full_name = f"{inferred.qname()}.{func.attrname}"
                if function_full_name in TARGETS_TO_FIND[schemaKey]:
                    idx = TARGETS_TO_FIND[schemaKey].index(function_full_name)
                    arg_param = PARAMS[idx]
                    self.add_message('proposed-removed-parameters', node=node, args=(arg_param, function_full_name,))
                    break
        except astroid.InferenceError:
            print("InferenceError")
            pass

class ParameterAddedRequiredChecker(checkers.BaseChecker):
    schemaKey = 'ParameterAddedRequired'
    FUNCTIONS_TO_FIND = [i.split('.')[-1] for i in TARGETS_TO_FIND[schemaKey]]
    PARAMS = PARAMS_TO_FIND[schemaKey]


    __implements__ = (interfaces.IAstroidChecker,)

    name = 'parameter-added-checker'
    priority = -1
    msgs = {
        'W0011': (
            'Found use of %s in func %s',
            'proposed-added-parameters',
            'This parameter is a new parameter that has been addeded a required argument',
        ),
    }

    def visit_call(self, node):
        func = node.func
        if not isinstance(func, astroid.Attribute) or (func.attrname not in FUNCTIONS_TO_FIND):
            return
        try:
            inferred_values = list(func.expr.infer())
            for inferred in inferred_values:
                if inferred is astroid.Uninferable:
                    print(f"Uninferable error: inferred {inferred} in {inferred_values}, with {func.attrname}")
                    continue
                function_full_name = f"{inferred.qname()}.{func.attrname}"
                if function_full_name in TARGETS_TO_FIND[schemaKey]:
                    idx = TARGETS_TO_FIND[schemaKey].index(function_full_name)
                    arg_param = PARAMS[idx]
                    self.add_message('proposed-added-parameters', node=node, args=(arg_param, function_full_name,))
                    break
        except astroid.InferenceError:
            print("InferenceError")
            pass


class ParameterMovedChecker(checkers.BaseChecker):
    schemaKey = 'ParameterMoved'
    FUNCTIONS_TO_FIND = [i.split('.')[-1] for i in TARGETS_TO_FIND[schemaKey]]
    PARAMS = PARAMS_TO_FIND[schemaKey]


    __implements__ = (interfaces.IAstroidChecker,)

    name = 'moved-parameters-checker'
    priority = -1
    msgs = {
        'W0012': (
            'Found use of %s in func %s',
            'moved-parameters',
            'This parameter has moved',
        ),
    }

    def visit_call(self, node):
        func = node.func
        if not isinstance(func, astroid.Attribute) or (func.attrname not in FUNCTIONS_TO_FIND):
            return
        try:
            inferred_values = list(func.expr.infer())
            for inferred in inferred_values:
                if inferred is astroid.Uninferable:
                    print(f"Uninferable error: inferred {inferred} in {inferred_values}, with {func.attrname}")
                    continue
                function_full_name = f"{inferred.qname()}.{func.attrname}"
                if function_full_name in TARGETS_TO_FIND[schemaKey]:
                    idx = TARGETS_TO_FIND[schemaKey].index(function_full_name)
                    arg_param = PARAMS[idx]
                    self.add_message('moved-parameters', node=node, args=(arg_param, function_full_name,))
                    break
        except astroid.InferenceError:
            print("InferenceError")
            pass

class ParameterChangedDefaultChecker(checkers.BaseChecker):
    schemaKey = 'ParameterChangedDefault'
    FUNCTIONS_TO_FIND = [i.split('.')[-1] for i in TARGETS_TO_FIND[schemaKey]]
    PARAMS = PARAMS_TO_FIND[schemaKey]


    __implements__ = (interfaces.IAstroidChecker,)

    name = 'changed-default-parameter'
    priority = -1
    msgs = {
        'W0013': (
            'Found use of %s in func %s',
            'changed-parameter',
            'This parameter has been changed in the new version of this package',
        ),
    }

    def visit_call(self, node):
        func = node.func
        if not isinstance(func, astroid.Attribute) or (func.attrname not in FUNCTIONS_TO_FIND):
            return
        try:
            inferred_values = list(func.expr.infer())
            for inferred in inferred_values:
                if inferred is astroid.Uninferable:
                    print(f"Uninferable error: inferred {inferred} in {inferred_values}, with {func.attrname}")
                    continue
                function_full_name = f"{inferred.qname()}.{func.attrname}"
                if function_full_name in TARGETS_TO_FIND[schemaKey]:
                    idx = TARGETS_TO_FIND[schemaKey].index(function_full_name)
                    arg_param = PARAMS[idx]
                    self.add_message('changed-parameter', node=node, args=(arg_param, function_full_name,))
                    break
        except astroid.InferenceError:
            print("InferenceError")
            pass

def register(linter):
    linter.register_checker(ParameterRemovedChecker(linter))
    linter.register_checker(ParameterAddedRequiredChecker(linter))
    linter.register_checker(ParameterMovedChecker(linter))
    linter.register_checker(ParameterChangedDefaultChecker(linter))
