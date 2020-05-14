# this script compiles passed dataset and then lift it to llvm ir
# works only on linux
# expected that already installed mcsema, wine, ida7, clang and llvm-dis and
# ida was configured, see ida_setup.txt for this
# please specify flags before run
# also you must place file template_vars.py to directory where you run this script

from threading import Thread
from absl import flags
import os
import sys
import random
import subprocess
import template_vars

flags.DEFINE_integer('ir_per_file', 8, 'Number of .ll files generated per input')
flags.DEFINE_string('compiler_flags', '', 'Additional compiler flags')
flags.DEFINE_integer('num_classes', 104, 'Number of classes to generate .ll')
flags.DEFINE_integer('num_samples', 200, 'Number samples per class')
flags.DEFINE_integer('num_threads', 10, 'Number of threads for run')
flags.DEFINE_string('dataset_path', '/home/vladimir/programming/tmp/programs/ProgramData', 'Path to dataset')
flags.DEFINE_string('ida_path', '\"/home/vladimir/.wine/drive_c/Program Files/IDA 7.2/idat64.exe\"',
	 'path to ida.exe with escaped path')
flags.DEFINE_string('llvm_dis', 'llvm-dis-6.0', 'path to llvm-dis')
flags.DEFINE_string('mcsema_lift', 'mcsema-lift-4.0', 'path mcsema-lift')
FLAGS = flags.FLAGS
FLAGS(sys.argv)

class CompilerArgumentGenerator(object):
    def __init__(self):
        self.compiler = template_vars.ValueListVar(
            ['g++ -w -std=c++11', 'clang++ -w -std=c++11'])
        self.optimization = template_vars.ValueListVar(['-O0','-O1','-O2','-O3'])
        self.fastmath = template_vars.ValueListVar(['', '-ffast-math'])
        self.native = template_vars.ValueListVar(['', '-march=native'])

    # Returns a tuple (cmdline, output_filename) -- for indexing purposes
    def get_cmdline(self, input_path, outpath, input_filename, additional_flags):        
        # file.cpp -> file_RANDOM.elf
        output_filename = (input_filename[:-4] + '_' +
                           template_vars.RandomStrVar()[0] + '.elf')
        output_path = os.path.join(outpath, output_filename)

        args = [self.compiler, self.optimization, self.fastmath, self.native]
        arg_strs = [str(random.choice(arg)) for arg in args]
        return (' '.join(arg_strs) + ' ' + input_path + '/' + input_filename + 
                ' ' + additional_flags + ' -o ' + output_path), output_filename

def _createdir(dname):
    try:
        os.makedirs(dname)
    except FileExistsError:
        pass

def compile(inpath, binpath, file):
    cag = CompilerArgumentGenerator()
    
    filenames = []
    for i in range(FLAGS.ir_per_file):
        (cmdline, output_filename) = cag.get_cmdline(inpath, binpath, file, FLAGS.compiler_flags)
        ret_code = subprocess.call(cmdline, shell=True)
        if ret_code == 0:
            filenames.append(output_filename)
        else:
            filenames.append(-1)
    return filenames

def prepare(txtpath, file):
    includes = '#include <iostream>\n' + '#include <cstdio>\n' + 'using namespace std;\n' + \
        '#include <math.h>\n' + '#include <string.h>\n'
    cppfilename = os.path.join(txtpath, file[:-4] + '.cpp')
    with open(cppfilename, 'w') as f_out:
        with open(os.path.join(txtpath, file), 'r') as f_in:
            f_out.write(includes)
            while True:
                line = f_in.readline()
                if (len(line) == 0):
                    break

                if 'main(' in line:
                    if 'void' in line:
                        f_out.write(line.replace('void', 'int'))
                    elif not('int' in line):
                        f_out.write(line.replace('main', 'int main'))
                    else:
                        f_out.write(line)                        
                else:
                    f_out.write(line)
                
def lift(path, name, liftpath):
    ida_path = FLAGS.ida_path
    llvm_dis = FLAGS.llvm_dis
    mcsema_lift = FLAGS.mcsema_lift
    elf_path = os.path.join(path, name)
    cfg_path = os.path.join(liftpath, name[:-4] + '.cfg')
    bc_path = os.path.join(liftpath, name[:-4] + '.bc')
    ll_path = os.path.join(liftpath, name[:-4] + '.ll')

    mcsema_disass_cmd = 'wine ' + ida_path + ' -B -S\"get_cfg.py --output ' + cfg_path + \
        ' --arch amd64 --os linux --entrypoint main\" ' + elf_path
    subprocess.call(mcsema_disass_cmd, shell=True)

    mcsema_lift_cmd = mcsema_lift + ' --output ' + bc_path + ' --arch amd64 --os linux --cfg ' + cfg_path
    subprocess.call(mcsema_lift_cmd, shell=True)

    llvm_dis_cmd = llvm_dis + ' ' + bc_path + ' -o ' + ll_path
    subprocess.call(llvm_dis_cmd, shell=True)

    os.remove(cfg_path)
    os.remove(bc_path)

class MyThread(Thread):
    def __init__(self, binpath, liftpath, txtpath, listing):
        Thread.__init__(self)
        self.txtpath = txtpath
        self.binpath = binpath
        self.liftpath = liftpath
        self.listing = listing

    def run(self):
        for f in self.listing:
            prepare(self.txtpath, f)
            bin_filenames = compile(self.txtpath, self.binpath, f[:-4] + '.cpp')
            for i in range(len(bin_filenames)):
                if bin_filenames[i] == -1:
                    continue
                lift(self.binpath, bin_filenames[i], self.liftpath)
    
def create_threads():
    num_classes = FLAGS.num_classes
    num_samples = FLAGS.num_samples
    num_threads = FLAGS.num_threads
    path = FLAGS.dataset_path
    cwd = os.path.dirname(os.path.abspath(__file__))
    outpath = cwd + '/elf_files'
    _createdir(outpath)
    liftpath = cwd + '/lift_llvm_ir'
    _createdir(liftpath)
    
    for c in range(0, num_classes):
        threads = []
        print('Proccess {} class'.format(str(c + 1)))
        _outpath = os.path.join(outpath, str(c + 1))
        _createdir(_outpath)
        _liftpath = os.path.join(liftpath, str(c + 1))
        _createdir(_liftpath)
        
        class_path = os.path.join(path, str(c + 1))
        listing = [f for f in os.listdir(class_path) if f.endswith('.txt')]
        assert len(listing) >= num_samples, 'in folder {} to little samples,\
            please specify other value'.format(class_path)
        
        for i in range(num_threads):
            count_per_thread = (int)(num_samples / num_threads)
            threads.append(MyThread(_outpath, _liftpath, class_path, 
                listing[i * count_per_thread:(i + 1) * count_per_thread]))
            threads[i].start()
        for i in range(num_threads):
            threads[i].join(timeout=720.0)

if __name__ == "__main__":
    create_threads()