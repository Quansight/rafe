from pylint import run_pylint as Run
import astroid

#print(astroid.__version__)

config_file = "check_functions_only.cfg"
target = "test_for_pylint.py"
args = [target, f"--rcfile={config_file}"]
Run(args)
