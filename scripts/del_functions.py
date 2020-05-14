# this script delete functions in llvm ir dataset which have
# appeared during compilation and lifting
# please specify flags before run

import os
import sys
from threading import Thread
import cxxfilt
from absl import flags
flags.DEFINE_string('path_funcs', '/home/vtelepov/tmp2/task/classifyapplifted/cpp_functions', 
	'path to funcs declared in source files')
flags.DEFINE_string('path_llvm', '/home/vtelepov/tmp2/task/classifyapplifted/', 'path to llvm ir dataset')
flags.DEFINE_integer('num_classes', 104, 'Number of dataset classes')
flags.DEFINE_integer('num_threads', 32, 'Number of threads for run')
FLAGS = flags.FLAGS
FLAGS(sys.argv)

def get_mangled_funcs(_ll_file, _cpp_file):
	ll_file = open(_ll_file, 'r')
	functions = []
	with open(_cpp_file, 'r') as cppfile:
		functions = cppfile.read().split('\n')[:-1]

	mangled_funcs = []
	while True:
		line = ll_file.readline()
		if (len(line) == 0):
			break
		if line == '\n':
			continue

		tmp = line.split()
		if tmp[0] == 'define':
			func_name = line.split('@')[1].split('(')[0]
			try:
				if cxxfilt.demangle(func_name).split('(')[0] in functions:
					mangled_funcs.append(func_name)
			except:
				pass

	ll_file.close()
	return mangled_funcs

def del_funcs(_ll_file, _cpp_file):
	mangled_funcs = get_mangled_funcs(_ll_file, _cpp_file)
	ll_file = open(_ll_file, 'r')
	tmp_file = open(_ll_file + '.tmp', 'w')
	while True:
		line = ll_file.readline()
		if (len(line) == 0):
			break
		if line == '\n':
			continue

		tmp = line.split()
		if tmp[0] != 'define':
			tmp_file.write(line)
		else:
			not_presented = True
			func_name = line.split('@')[1].split('(')[0]
			
			for f in mangled_funcs:
				if (f == func_name) or ((f in func_name) and (func_name[:3] == 'sub')): 
					not_presented = False
				
			if not_presented:
				while True:
					line = ll_file.readline()
					if line == '}\n':
						break
			else:
				tmp_file.write(line)
			
		
	ll_file.close()
	tmp_file.close()
	os.remove(_ll_file)
	os.rename(_ll_file + '.tmp', _ll_file)

class MyThread(Thread):
	def __init__(self, cpppath, llpath, listing):
		Thread.__init__(self)
		self.cpppath = cpppath
		self.llpath = llpath
		self.listing = listing

	def run(self):
		for f in self.listing:
			del_funcs(os.path.join(self.llpath, f), os.path.join(self.cpppath, f.split('_')[0] + '.txt'))

def main():
	num_classes = FLAGS.num_classes
	num_threads = FLAGS.num_threads
	path_cpp = FLAGS.path_funcs
	path = [os.path.join(FLAGS.path_llvm, 'ir_test'), os.path.join(FLAGS.path_llvm, 'ir_val'), os.path.join(FLAGS.path_llvm, 'ir_train')]
	for path_in in path: 
		for c in range(num_classes):
			_path_cpp = os.path.join(path_cpp, str(c + 1))
			_path_in = os.path.join(path_in, str(c + 1))

			listing = os.listdir(_path_in)
			count_per_thread = (int)(len(listing) / num_threads)
			
			threads = []
			for i in range(num_threads - 1):
				threads.append(MyThread(_path_cpp, _path_in, listing[i * count_per_thread:(i + 1) * count_per_thread]))
				threads[i].start()
			threads.append(MyThread(_path_cpp, _path_in, listing[(num_threads - 1) * count_per_thread:]))
			threads[num_threads - 1].start()

			for i in range(num_threads):
				threads[i].join(timeout=720.0)

if __name__ == '__main__':
	main()