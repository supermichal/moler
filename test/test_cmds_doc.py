from importlib import import_module
from os import listdir, path, walk
from os.path import isfile, join, abspath, dirname

from mock import mock
from pytest import mark, raises

__author__ = 'Michal Plichta'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'michal.plichta@nokia.com'

# dir_path = path.dirname(path.realpath(__file__))
# moler_dir_path = path.join(path.dirname(dir_path), 'moler')
cmd_dir_under_test = 'moler/cmd/'



# --------------- helper functions ---------------
def _list_in_path(listing_type):
    """
    Quick and dirty function to return list of strings depends on parameter:
    - allfiles - list all file without path
    - fullpath  - list only py files with path
    - only_py  - list only py file without path

    :param listing_type:
    :return: list of files
    :rtype: list(str)
    """
    repo_path = abspath(join(dirname(__file__), '..'))
    abs_test_path = join(repo_path, cmd_dir_under_test)
    file_list = []


    if listing_type == 'allfiles':
        file_list = [f for root, dirs, files in walk(abs_test_path) for f in files if isfile(join(root, f))]
    elif listing_type == 'fullpath':
        file_list = [path.join(cmd_dir_under_test, path.basename(root), f) for root, dirs, files in walk(abs_test_path)
                     for f in files if isfile(join(root, f)) and '__init__' not in f and '.pyc' not in f]
    elif listing_type == 'only_py':
        file_list = [f for root, dirs, files in walk(abs_test_path)
                     for f in files if isfile(join(root, f)) and '__init__' not in f and '.pyc' not in f]

    return file_list

def _load_obj(func_name):
    """
    Load instance form module.

    :param func_name: function name as string
    :return: object instance
    :rtype: type
    """
    return getattr(import_module('moler.util.cmds_doc'), func_name)
# --------------- helper functions ---------------


def test_documentation_exists():
    from moler.util.cmds_doc import check_if_documentation_exists

    dir_path = path.dirname(path.realpath(__file__))
    moler_dir_path = path.dirname(dir_path)
    cmd_path = path.join(moler_dir_path, "moler", "cmd")

    assert check_if_documentation_exists(cmd_path) is True


def test_buffer_connection_returns_threadconnection_with_moler_conn():
    from moler.io.raw.memory import ThreadedFifoBuffer
    from moler.connection import ObservableConnection
    from moler.util.cmds_doc import _buffer_connection

    buff_conn = _buffer_connection()
    assert isinstance(buff_conn, ThreadedFifoBuffer) is True
    assert isinstance(buff_conn.moler_connection, ObservableConnection) is True


@mark.parametrize('func2test,method_param,expected', [
    ('_walk_moler_python_files', cmd_dir_under_test, True),
    ('_walk_moler_commands', cmd_dir_under_test, True),
    ('_walk_moler_nonabstract_commands', cmd_dir_under_test, True)])
def test_functions_are_generators(func2test, method_param, expected):
    from inspect import isgenerator, isgeneratorfunction

    func_obj = _load_obj(func_name=func2test)
    generator_obj = func_obj(method_param)

    assert isgeneratorfunction(func_obj) is expected
    assert isgenerator(generator_obj) is expected


def test_walk_moler_python_files_is_generator_return_all_files_in_dir():
    from moler.util.cmds_doc import _walk_moler_python_files

    file_list = _list_in_path(listing_type='fullpath')
    walker = _walk_moler_python_files(cmd_dir_under_test)

    list_from_generator = []
    for file in walker:
        list_from_generator.append(file)
    assert list_from_generator == file_list


def test_walk_moler_commands_is_generator_return_all_files_in_dir():
    from moler.util.cmds_doc import _walk_moler_commands
    from six.moves import zip

    file_list = _list_in_path(listing_type='only_py')
    walker = _walk_moler_commands(cmd_dir_under_test)

    list_from_generator = []
    for cmd, file in zip(walker, file_list):
        list_from_generator.append(cmd)

        assert file in str(cmd[0])
    assert len(list_from_generator) == len(file_list)


@mark.parametrize('func2test,method_param', [
    ('_walk_moler_python_files', cmd_dir_under_test),
    ('_walk_moler_commands', cmd_dir_under_test),
    ('_walk_moler_nonabstract_commands', cmd_dir_under_test)])
def test_genertors_return_files_without_dunder_init(func2test, method_param):
    func_obj = _load_obj(func_name=func2test)
    generator_obj = func_obj(method_param)
    file_list = _list_in_path(listing_type='allfiles')

    with raises(StopIteration):
        for _ in range(len(file_list)):
            next(generator_obj)


def test_walk_moler_nonabstract_commands_raise_exception_when_called(fake_cmd):
    from moler.util.cmds_doc import _walk_moler_nonabstract_commands

    with mock.patch('moler.util.cmds_doc._walk_moler_commands', return_value=(None, fake_cmd)):
        with raises(Exception):
            next(_walk_moler_nonabstract_commands(cmd_dir_under_test))


def test_retrieve_command_documentation_as_dict():
    from moler.util.cmds_doc import _retrieve_command_documentation

    fake_cmd_from_conftest = _retrieve_command_documentation(import_module('conftest'))
    assert isinstance(fake_cmd_from_conftest, dict)
    assert isinstance(fake_cmd_from_conftest['_ver_nice'], dict)
    assert isinstance(fake_cmd_from_conftest['_ver_nice']['COMMAND_OUTPUT'], str)
    assert isinstance(fake_cmd_from_conftest['_ver_nice']['COMMAND_KWARGS'], dict)
    assert isinstance(fake_cmd_from_conftest['_ver_nice']['COMMAND_RESULT'], dict)


def test_validate_documentation_existence():
    from moler.util.cmds_doc import _validate_documentation_existence
    fake_cmd = import_module('conftest')

    test_data = {'_ver_execute': {'COMMAND_OUTPUT': '', 'COMMAND_KWARGS': {}, 'COMMAND_RESULT': {}},
                 '_ver_test': {'COMMAND_OUTPUT': '', 'COMMAND_KWARGS': {}, 'COMMAND_RESULT': {}}}
    assert _validate_documentation_existence(fake_cmd, test_data) == ''

    missing = _validate_documentation_existence(fake_cmd, {})
    assert 'conftest' in missing
    assert 'is missing documentation: COMMAND_OUTPUT/COMMAND_KWARGS/COMMAND_RESULT' in missing


def test_validate_documentation_consistency():
    from moler.util.cmds_doc import _validate_documentation_consistency
    fake_cmd = import_module('conftest')

    test_data = {'_ver_test1': {'COMMAND_KWARGS': {}, 'COMMAND_RESULT': {}},
                 '_ver_test2': {'COMMAND_OUTPUT': '', 'COMMAND_RESULT': {}},
                 '_ver_test3': {'COMMAND_OUTPUT': '', 'COMMAND_KWARGS': {}}}
    result1 = _validate_documentation_consistency(fake_cmd, test_data, '_ver_test1')
    result2 = _validate_documentation_consistency(fake_cmd, test_data, '_ver_test2')
    result3 = _validate_documentation_consistency(fake_cmd, test_data, '_ver_test3')

    assert isinstance(result1, list)
    assert isinstance(result2, list)
    assert isinstance(result3, list)
    assert "<module 'conftest'" in result1[0] and "<module 'conftest'" in result1[0]
    assert "<module 'conftest'" in result2[0] and "<module 'conftest'" in result2[0]
    assert "<module 'conftest'" in result3[0] and "<module 'conftest'" in result3[0]
    assert '> has COMMAND_KWARGS_ver_test1 but no COMMAND_OUTPUT_ver_test1' in result1[0]
    assert '> has COMMAND_RESULT_ver_test1 but no COMMAND_OUTPUT_ver_test1' in result1[1]
    assert '> has COMMAND_OUTPUT_ver_test2 but no COMMAND_KWARGS_ver_test2' in result2[0]
    assert '> has COMMAND_RESULT_ver_test2 but no COMMAND_KWARGS_ver_test2' in result2[1]
    assert '> has COMMAND_OUTPUT_ver_test3 but no COMMAND_RESULT_ver_test3' in result3[0]
    assert '> has COMMAND_KWARGS_ver_test3 but no COMMAND_RESULT_ver_test3' in result3[1]


def test_get_doc_variant():
    from moler.util.cmds_doc import _get_doc_variant

    test_data = {'_ver_test1': {'COMMAND_OUTPUT': 'out1', 'COMMAND_KWARGS': {1: 1}, 'COMMAND_RESULT': {1: 1}},
                 '_ver_test2': {'COMMAND_OUTPUT': 'out2', 'COMMAND_RESULT': {2: 2}}}
    result1 = _get_doc_variant(test_data, '_ver_test1')
    result2 = _get_doc_variant(test_data, '_ver_test2')

    assert result1 == ('out1', {1: 1}, {1: 1})
    assert result2 == ('out2', {}, {2: 2})


def test_create_command_raise_exception_when_object_takes_no_params(fake_cmd):
    from moler.util.cmds_doc import _create_command, _buffer_connection

    with raises(Exception) as exc:
        _create_command(fake_cmd, _buffer_connection().moler_connection, {})

    assert "via FakeCommand() : object() takes no parameters" or "via FakeCommand() : this constructor takes no arguments" in str(exc.value)


def test_create_command_success(nice_cmd):
    from moler.util.cmds_doc import _create_command, _buffer_connection

    result = _create_command(nice_cmd, _buffer_connection().moler_connection, {'nice': 'nice'})
    assert isinstance(result[0], nice_cmd)
    assert result[1] == 'NiceCommand(nice=nice)'


def test_run_command_parsing_test_success(nice_cmd):
    # ToDo: not finished
    from moler.util.cmds_doc import _run_command_parsing_test, _buffer_connection, _get_doc_variant, _create_command
    buffer_io = _buffer_connection()
    variant = '_ver_nice'
    test_data = {variant: {'COMMAND_OUTPUT': 'nice', 'COMMAND_KWARGS': {'nice': 'nice'}, 'COMMAND_RESULT': {'nice': 'nice'}}}

    cmd_output, cmd_kwargs, cmd_result = _get_doc_variant(test_data, variant)
    moler_cmd, creation_str = _create_command(nice_cmd, buffer_io.moler_connection, cmd_kwargs)
    _run_command_parsing_test(nice_cmd, creation_str, buffer_io, cmd_output, cmd_result, variant)
