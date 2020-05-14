# this script get function names from specified dataset
# excepted that clang is installed
# please specify flags before run

import clang.cindex
import typing
import os
import sys
from shutil import copyfile

from absl import flags
flags.DEFINE_string('lib_path', '/usr/lib/llvm-6.0/lib', 'path to clang library')
flags.DEFINE_string('path_in', '/home/vladimir/programming/tmp/programs/ProgramData', 'path to dataset .cpp files')
flags.DEFINE_string('path_out', '/home/vladimir/programming/tmp/cpp_functions', 'path to put funcs from dataset')
flags.DEFINE_integer('num_classes', 104, 'Number of classes in dataset')
FLAGS = flags.FLAGS
FLAGS(sys.argv)


def get_func_names_from_file(file_path):
    def filter_node_list_by_kind(
            nodes: typing.Iterable[clang.cindex.Cursor],
            kinds: list
    ) -> typing.Iterable[clang.cindex.Cursor]:
        result = []
        for node in nodes:
            if node.kind in kinds:
                result.append(node)

        return result

    index = clang.cindex.Index.create()
    try:
        translation_units = index.parse(file_path, args=["-O0"])
    except:
        print("failed to compile {} file".format(file_path))
        return []

    funcs = filter_node_list_by_kind(translation_units.cursor.get_children(), [clang.cindex.CursorKind.FUNCTION_DECL])
    func_names = [func.spelling for func in funcs]
    return list(set(func_names))


def extract_funcs(name_in, name_out):
    funcs = get_func_names_from_file(name_in)

    with open(name_out, 'w') as f_out:
        for func in funcs:
            f_out.write(func + '\n')


def _createdir(dname):
    try:
        os.makedirs(dname)
    except FileExistsError:
        pass


def main():
    clang.cindex.Config.set_library_path(FLAGS.lib_path)
    path_in = FLAGS.path_in
    path_out = FLAGS.path_out
    num_classes = FLAGS.num_classes
    _createdir(path_out)
    for c in range(num_classes):
        _path_in = os.path.join(path_in, str(c + 1))
        _path_out = os.path.join(path_out, str(c + 1))
        _createdir(_path_out)

        listing = [f for f in os.listdir(_path_in) if f.endswith('.cpp')]
        for i in range(len(listing)):
            c_path_in = os.path.join(_path_in, listing[i])
            extract_funcs(c_path_in, os.path.join(_path_out, listing[i][:-4] + '.txt'))


if __name__ == '__main__':
    main()
