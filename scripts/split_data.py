# this script generate train, test and validation datasets from given dataset
# it places it co current directory to folders llvm_ir_train, llvm_ir_test, llvm_ir_val

import os
import sys
from shutil import copyfile
from absl import flags
flags.DEFINE_string('path', '/home/vladimir/programming/tmp/lift_llvm_ir', 'path to datset')
flags.DEFINE_integer('num_classes', 104, 'Number of dataset classes')
FLAGS = flags.FLAGS
FLAGS(sys.argv)

def _createdir(dname):
    try:
        os.makedirs(dname)
    except FileExistsError:
        pass

def main():
    path = FLAGS.path
    num_clusses = FLAGS.num_classes
    _createdir('ir_train')
    _createdir('ir_val')
    _createdir('ir_test')
    parts = [0.6, 0.2, 0.2]
    for c in range(num_clusses):
        _path = os.path.join(path, str(c + 1))
        _path_train = os.path.join('ir_train', str(c + 1))
        _path_val = os.path.join('ir_val', str(c + 1))
        _path_test = os.path.join('ir_test', str(c + 1))
        _createdir(_path_train)
        _createdir(_path_val)
        _createdir(_path_test)

        listing = os.listdir(_path)
        f.write('{}: {}\n'.format(c + 1, len(listing)))
        size = min(num_samples, len(listing))
        sizes = [int(size * p) for p in parts]
        for i in range(sizes[0]):
            copyfile(os.path.join(_path, listing[i]), os.path.join(_path_train, listing[i]))
        for i in range(sizes[1]):
            copyfile(os.path.join(_path, listing[sizes[0] + i]), os.path.join(_path_val, listing[sizes[0] + i]))
        for i in range(sizes[2]):
            copyfile(os.path.join(_path, listing[sizes[0] + sizes[1] + i]), os.path.join(_path_test, listing[sizes[0] + sizes[1] + i]))
    f.close()  

if __name__ == "__main__":
    main()