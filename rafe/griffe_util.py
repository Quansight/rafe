import griffe
import json
import re
import pathlib
import logging
import importlib

def parse_attribute_error(error_msg):
    pattern = r"module '([\w\.]+)' has no attribute '(\w+)'"
    match = re.search(pattern, error_msg)
    if match:
        return match.groups()
    else:
        return None, None

def recursive_attempt_import_eval(i,e,the_package,call,call_descript,actual_misses,logger):
     
    if isinstance(logger, logging.Logger):
        ...
    else:
        logger = logging.getLogger(__name__)
    
    logger.info(f"raised AttributeError {e}")
    module_name, missing_attribute = parse_attribute_error(e.args[0])
    #logger.info(f"Read as module: {module_name}, attribute: {missing_attribute}")
    if module_name is not None:
        try:
            logger.info(f"attempting to import {module_name}.{missing_attribute}")
            globals()[f"{module_name}.{missing_attribute}"] = importlib.import_module(f"{module_name}.{missing_attribute}")
            if f"{module_name}.{missing_attribute}" in globals():
                logger.info(f"Correctly imported {module_name}.{missing_attribute}")
            try:
                evaluation = eval(call)
                if not evaluation:
                    logger.info(f"{call_descript} evals false, actually missing")
                    actual_misses.append(f"{i}")
                    return actual_misses
                else:
                    logger.info(f"{call_descript} evals {evaluation}")
            except Exception as e: 
                if isinstance(e,AttributeError):
                    actual_misses = recursive_attempt_import_eval(i,e,the_package,call,call_descript,actual_misses,logger)
                else:
                    logger.info(f"{i}: {e}")
                    actual_misses.append(f"{i}")
                    return actual_misses
        except:
            logger.info(f"{i}: {e}")
            actual_misses.append(f"{i}")
            return actual_misses
    else:
        logger.info(f"{i}: {e}")
        actual_misses.append(f"{i}")
        return actual_misses

    return actual_misses

def check_breaks(package, old_tag, new_tag, path_to_package, break_type, output_path, logger):
    
    if isinstance(logger, logging.Logger):
        ...
    else:
        logger = logging.getLogger(__name__)

    previous = griffe.load_git(package, repo=path_to_package, ref=old_tag)
    current = griffe.load_git(package, repo=path_to_package, ref=new_tag)

    breaks = [breakage for breakage in griffe.find_breaking_changes(previous, current)]

    removed_objects = [j.as_dict() for j in breaks if isinstance(j,griffe.diff.ObjectRemovedBreakage)]
    removed_objects = [j['object_path'] for j in removed_objects if not (j['object_path'][-2:] == "/*")]
    #second remove_objects line catches griffe alias types, that produce obj paths like numpy.fft.numpy/fft/name/*
    object_kind = [j.as_dict()['object_path'] for j in breaks if isinstance(j,griffe.diff.ObjectChangedKindBreakage)]
    attribute_changed = [j.as_dict()['object_path'] for j in breaks if isinstance(j,griffe.diff.AttributeChangedValueBreakage)]
    param_moved = [(j.as_dict()['object_path'],j.as_dict()['old_value'].as_dict()['name']) for j in breaks if isinstance(j,griffe.diff.ParameterMovedBreakage)]
    param_added = [(j.as_dict()['object_path'],j.as_dict()['new_value'].as_dict()['name']) for j in breaks if isinstance(j,griffe.diff.ParameterAddedRequiredBreakage)]
    param_removed = [(j.as_dict()['object_path'],j.as_dict()['old_value'].as_dict()['name']) for j in breaks if isinstance(j,griffe.diff.ParameterRemovedBreakage)]
    param_changed = [(j.as_dict()['object_path'],j.as_dict()['old_value'].as_dict()['name']) for j in breaks if isinstance(j,griffe.diff.ParameterChangedDefaultBreakage)]

    all_typed_breaks = {"ObjectRemoved":removed_objects,
                        "ObjectChangedKind":object_kind,
                        "AttributeChangedValue":attribute_changed,
                        "ParameterMoved":param_moved,
                        "ParameterAddedRequired":param_added,
                        "ParameterRemoved":param_removed,
                        "ParameterChangedDefault":param_changed}

    #example to filter to just functions removed:
    #function_breaks = [i["object_path"] for i in types_compare if isinstance(i["old_value"],griffe.dataclasses.Function)]

    output_json = pathlib.Path(output_path).joinpath(f"{package}_api_breaks.json")
    with open(output_json, "w") as write_file:
        json.dump(all_typed_breaks, write_file)
        logger.info(f"{output_json} written to file.")

    return


def verify_removals(package_name, file_path, logger):
    
    if isinstance(logger, logging.Logger):
        ...
    else:
        logger = logging.getLogger(__name__)

    the_package = importlib.import_module(package_name)
    
    try:
        package_version = the_package.__version__
        logger.info(f"{package_name} Version: {package_version}")
    except:
        logger.info(f"Unable to read version info from {package_name}")

    if pathlib.Path(file_path).exists():
        with open(pathlib.Path(file_path),'r') as f:
            breaks_all = json.load(f)
        breaks = breaks_all["ObjectRemoved"]
    else:
        logger.error(f"Unable to load {file_path}, pathlib says it doesn't exist.")
        return 0

    actual_misses = []
    for i in breaks:
        stub = '.'.join(i.split('.')[:-1])  # e.g. strips np.lib.npyio.NpzFile to np.lib.npyio
        stub_call = "the_package"+'.'+'.'.join(stub.split('.')[1:]) # replaces np with 'the_package' for local ref
        call = f"hasattr({stub_call},'{i.split('.')[-1]}')"
        call_descript = f"hasattr({stub},'{i.split('.')[-1]}')"
        try:
            evaluation = eval(call)
            if not evaluation:
                logger.info(f"{call_descript} evals false, actually missing")
                actual_misses.append(f"{i}")
            else:
                logger.info(f"{call_descript} evals {evaluation}")
        except Exception as e:
            if isinstance(e,AttributeError):
                actual_misses = recursive_attempt_import_eval(i,e,the_package,call,call_descript,actual_misses,logger)
            else:
                logger.info(f"{i}: {e}")            
                actual_misses.append(f"{i}")

    breaks_all["ObjectRemoved"] = actual_misses
    out_file = pathlib.Path(file_path).parent.joinpath(f"{package_name}_verified_removed_objects.json")
    with open(out_file, "w") as f:
        json.dump(breaks_all, f)

    return
