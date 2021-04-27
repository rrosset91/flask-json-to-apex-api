from argparse import ArgumentParser, FileType
import json
from operator import itemgetter
from os import access, linesep, makedirs, path as os_path, W_OK
from iso8601 import parse_date

class_definitions = []
class_props = {}


def json2apex(className, generateTest, jsonContent, auraEnabled, parseMethod):
    clearDefinitions()
    if generateTest == 'true':
        generateTest = True
    if auraEnabled == 'true':
        auraEnabled = True
    if generateTest == 'false':
        generateTest = False
    if auraEnabled == 'false':
        auraEnabled = False
    if parseMethod == 'false':
        parseMethod = False
    if parseMethod == 'true':
        parseMethod = True

    jsonContent = json.loads(jsonContent)
    return main(jsonContent, className, generateTest, 3, auraEnabled, parseMethod)


def writeable_dir(prospective_dir):
    if not os_path.exists(prospective_dir):
        makedirs(prospective_dir)
    if not os_path.isdir(prospective_dir):
        raise Exception('{0} is not a valid path'.format(prospective_dir))
    if access(prospective_dir, W_OK):
        return prospective_dir
    else:
        raise Exception('{0} is not a writable dir'.format(prospective_dir))


def create_class_def(k):
    name = '' + k.capitalize()
    if name in class_definitions:
        i = 2
        while name + str(i) in class_definitions:
            i += 1
        name += str(i)
    class_definitions.append(name)
    class_props[name] = {}
    return name


def apex_type(k, v):
    if v is None:
        return 'String'
    elif isinstance(v, str):
        try:
            parse_date(v)
            return 'DateTime'
        except:
            return 'String'
    elif isinstance(v, bool):
        return 'Boolean'
    elif isinstance(v, int):
        return 'Integer'
    elif isinstance(v, float):
        return 'Double'
    elif isinstance(v, list):
        if len(v) > 0:
            return 'List<{0}>'.format(apex_type(k, v[0]))
        else:
            return
    elif isinstance(v, dict):
        class_name = create_class_def(k)
        process(v, class_name)
        return class_name


def process(obj, parent):
    for k, v in obj.items():
        class_props[parent][k] = apex_type(k, v)


def write_class_open(out, cls, num_spaces):
    indent = ' ' * num_spaces
    out += '{0}public class {1} {{{2}'.format(indent, cls, linesep)
    return out


def write_class_close(out, num_spaces):
    indent = ' ' * num_spaces
    out += '{0}}}{1}'.format(indent, linesep)
    return out


def write_class_props(out, props, num_spaces, auraEnabled):
    indent = ' ' * num_spaces
    if auraEnabled:
        for k, v in props:
            out += '{0}@AuraEnabled public {1} {2};{3}'.format(indent, v, k, linesep)
    else:
        for k, v in props:
            out += '{0}public {1} {2};{3}'.format(indent, v, k, linesep)
    return out


def write_parse_method(out, cls, num_spaces):
    indent = ' ' * num_spaces
    out += '{0}public static {1} parse(String json) {{{2}'.format(indent, cls, linesep)
    out += '{0}return ({1})System.JSON.deserialize(json, {2}.class);{3}'.format(indent * 2, cls, cls, linesep)
    out += '{0}}}{1}'.format(indent, linesep)
    return out


def write_test_class(out, cls, json_dict, num_spaces):
    indent = ' ' * num_spaces
    json_str = json.dumps(json_dict, indent=' ' * num_spaces)
    json_str = (' + ' + linesep).join(["{0}'{1}'".format(indent * 2, line) for line in json_str.split(linesep)])
    out += '@isTest{0}'.format(linesep)
    out += 'public class Test{0} {{{1}'.format(cls, linesep)
    out += '{0}@isTest{1}'.format(indent, linesep)
    out += '{0}public static void testParse() {{{1}'.format(indent, linesep)
    out += '{0}String json = {1};{2}'.format(indent * 2, json_str, linesep)
    out += '{0}{1} obj = {2}.parse(json);{3}'.format(indent * 2, cls, cls, linesep)
    out += '{0}System.assertNotEquals(null, obj);{1}'.format(indent * 2, linesep)
    out += '{0}}}{1}'.format(indent, linesep)
    out += '}}{0}'.format(linesep)
    return out


def clearDefinitions():
    global class_definitions
    class_definitions = []
    global class_props
    class_props = {}


def main(input_json, class_name, generate_test, indent_spaces, auraEnabled, parseMethod):
    clearDefinitions()
    json_dict = json.loads(input_json)
    class_definitions.append(class_name)
    class_props[class_name] = {}
    process(json_dict, parent=class_name)
    out = ''
    out = write_class_open(out, class_name, 0)
    sorted_props = sorted(class_props[class_name].items(), key=itemgetter(0))
    out = write_class_props(out, sorted_props, indent_spaces, auraEnabled)
    write_class_props(out, sorted_props, indent_spaces, auraEnabled)
    for cls in sorted(class_definitions):
        if cls == class_name:
            continue
        out = write_class_open(out, cls, indent_spaces)
        sorted_props = sorted(class_props[cls].items(), key=itemgetter(0))
        out = write_class_props(out, sorted_props, indent_spaces * 2, auraEnabled)
        out = write_class_close(out, indent_spaces)
    if parseMethod:
        out = write_parse_method(out, class_name, indent_spaces)
    out = write_class_close(out, indent_spaces)
    wrapper_class_content = out
    test_class_content = ''

    if generate_test:
        test_out = ''
        test_out = write_test_class(test_out, class_name, json_dict, indent_spaces)
        test_class_content = test_out
        results = get_results(wrapper_class_content, test_class_content)
        return {"testClass": results.test, "wrapperClass": results.wrapper}
    else:
        results = get_results(wrapper_class_content, test_class_content)
        return {"wrapperClass": results.wrapper}


def get_results(wrapper, test):
    class Content:
        def __init__(self, return_wrapper, return_test):
            self.wrapper = return_wrapper
            self.test = return_test

    return_content = Content(wrapper.replace('\n\n', '\n'), test.replace('\n\n', '\n'))
    return return_content
