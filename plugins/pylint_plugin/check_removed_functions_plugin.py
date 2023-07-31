import astroid
import json
from pylint import checkers, interfaces

print(f"Astroid version: {astroid.__version__}")

def get_function_targets(key: str):
    with open("numpy_verified_removed_objects.json", 'r') as f:
        obj = json.load(f)
        TARGETS_TO_FIND = obj[key]
        print(f'Loaded {len(TARGETS_TO_FIND)}')
        return TARGETS_TO_FIND
    
TARGETS_TO_FIND = get_function_targets('ObjectRemoved')
FUNCTIONS_TO_FIND = [i.split('.')[-1] for i in TARGETS_TO_FIND]

class RemovedObjectsChecker(checkers.BaseChecker):
    __implements__ = (interfaces.IAstroidChecker,)

    name = 'removed-functions-checker'
    priority = -1
    msgs = {
        'W0001': (
            'Found use of %s',
            'proposed-removed-functions',
            'Anticipated removal of function in package update',
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
                if function_full_name in TARGETS_TO_FIND:
                    self.add_message('proposed-removed-functions', node=node, args=(function_full_name,))
                    break
        except astroid.InferenceError:
            print("InferenceError")
            pass

CHANGED_TARGETS_TO_FIND = get_function_targets('ObjectChangedKind')
CHANGED_FUNCTIONS_TO_FIND = [i.split('.')[-1] for i in CHANGED_TARGETS_TO_FIND]

class ChangedObjectsChecker(checkers.BaseChecker):
    __implements__ = (interfaces.IAstroidChecker,)

    name = 'changed-objects-checker'
    priority = -1
    msgs = {
        'W0002': (
            'Found use of %s',
            'changed-functions',
            'This function has changed',
        ),
    }

    def visit_call(self, node):
        func = node.func
        if not isinstance(func, astroid.Attribute) or (func.attrname not in CHANGED_FUNCTIONS_TO_FIND):
            return
        try:
            inferred_values = list(func.expr.infer())
            for inferred in inferred_values:
                if inferred is astroid.Uninferable:
                    print(f"Uninferable error: inferred {inferred} in {inferred_values}, with {func.attrname}")
                    continue
                function_full_name = f"{inferred.qname()}.{func.attrname}"
                if function_full_name in CHANGED_TARGETS_TO_FIND:
                    self.add_message('changed-functions', node=node, args=(function_full_name,))
                    break
        except astroid.InferenceError:
            print("InferenceError")
            pass

CHANGED_TARGETS_ATTRS_TO_FIND = get_function_targets('AttributeChangedValue')
CHANGED_ATTRIBUTES_TO_FIND = [i.split('.')[-1] for i in CHANGED_TARGETS_ATTRS_TO_FIND]

class ChangedAttributeChecker(checkers.BaseChecker):
    __implements__ = (interfaces.IAstroidChecker,)

    name = 'changed-attributes-checker'
    priority = -1
    msgs = {
        'W0003': (
            'Found use of %s',
            'changed-attribute',
            'these attributes will be changed in the newer package.',
        ),
    }

    def visit_call(self, node):
        func = node.func
        if not isinstance(func, astroid.Attribute) or (func.attrname not in CHANGED_TARGETS_ATTRS_TO_FIND):
            return
        try:
            inferred_values = list(func.expr.infer())
            for inferred in inferred_values:
                if inferred is astroid.Uninferable:
                    print(f"Uninferable error: inferred {inferred} in {inferred_values}, with {func.attrname}")
                    continue
                function_full_name = f"{inferred.qname()}.{func.attrname}"
                if function_full_name in CHANGED_TARGETS_ATTRS_TO_FIND:
                    self.add_message('changed-attribute', node=node, args=(function_full_name,))
                    break
        except astroid.InferenceError:
            print("InferenceError")
            pass


def register(linter):
    linter.register_checker(RemovedObjectsChecker(linter))
    linter.register_checker(ChangedObjectsChecker(linter))
    linter.register_checker(ChangedAttributeChecker(linter))



