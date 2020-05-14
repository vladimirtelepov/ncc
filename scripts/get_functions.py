# this script gets all functions from specified .ll file
# you must at first create folder tmp in current directory
# then scripts create one file per function

import sys
import os

def main():
	ll_file = open(sys.argv[1], 'r')
	assert os.path.isdir('tmp'), 'you must create tmp folder in current directory'
	while True:
		line = ll_file.readline()
		if (len(line) == 0):
			break

		if line == '\n':
			continue
		tmp = line.split()
		if tmp[0] != 'define':
			continue

		func_name = line.split('@')[1].split('(')[0]
		func_file = open(os.path.join('tmp', func_name) + '.ll', 'w')
		while True:
			func_file.write(line)
			line = ll_file.readline()
			if line == '}\n':
				func_file.write(line)
				break
		
		func_file.close()

	ll_file.close()

if __name__ == '__main__':
	main()