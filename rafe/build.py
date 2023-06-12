import os
import sys
import subprocess 
from os.path import isfile, join

from rafe.logger import logger 
import rafe.source as source


def get_environ():
    d = dict(os.environ)
    d['PREFIX'] = sys.prefix
    d['PYTHON'] = sys.executable
    return d

def ensure_build_dir_exists(recipe_dir, package):
	"""
	If the build directory exists, return true. Otherwise, raise an error.
	"""
	pass


def build_package(recipe_dir):
	"""
	Builds a package for the platform that is being used to build. 
	"""
	
	source.provide(recipe_dir)
	src_dir = source.get_dir()

	logger.info(f"""
	Building Pacakge: {recipe_dir}
	Source Tree: 	  {src_dir}
	""")

	env = get_environ()

	if sys.platform == 'win32':
		vcvarsall = (r'C:\Program Files (x86)\Microsoft Visual Studio 14.0'
                     r'\VC\vcvarsall.bat')
		assert isfile(vcvarsall)

		with open(join(recipe_dir, 'bld.bat')) as fi:
			data = fi.read()
			logger.debug(f"Read File {join(recipe_dir, 'bld.bat')} [green] SUCCESS [/green]")

		with open(join(src_dir, 'bld.bat'), 'w') as fo:
            # more debuggable with echo on
			fo.write('@echo on\n')
			for kv in env.items():
				fo.write('set %s=%s\n' % kv)
				fo.write('call "%s" amd64\n' % vcvarsall)
				fo.write(":: --- end generated header ---\n")
				fo.write(data)
		
		cmd = [os.environ['COMSPEC'], '/c', 'bld.bat']
		subprocess.check_call(cmd, cwd=src_dir)

	else:

		cmd = ['/bin/bash', '-x', '-e', recipe_dir.joinpath('build.sh')]
		
		build_process = subprocess.Popen(cmd, env=env, cwd=src_dir, stdout=subprocess.PIPE, bufsize=1)
		log_relative_filename = f"[bold cyan] {recipe_dir.name}" + "/build.sh" + "[/bold cyan] | " 
		for line in build_process.stdout:
			logger.info(log_relative_filename + line.decode('UTF-8').strip('\n'), extra={"markup": True})

		build_process.wait()
		if build_process.returncode != 0:
			raise OSError(build_process.returncode) 	

		logger.info(f'Build of {recipe_dir.name} [bold green] SUCCESS [/bold green] :boom:', extra={"markup": True})
		return 0

		
