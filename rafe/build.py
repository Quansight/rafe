import os
import sys
from subprocess import check_call
from os.path import isfile, join

from rafe.config import recipes_dir
import rafe.source as source


def get_environ():
    d = dict(os.environ)
    d['PREFIX'] = sys.prefix
    d['PYTHON'] = sys.executable
    return d


def build(recipe_dir):
    source.provide(recipe_dir)
    src_dir = source.get_dir()
    print("source tree in:", src_dir)
    env = get_environ()

    if sys.platform == 'win32':
        vcvarsall = (r'C:\Program Files (x86)\Microsoft Visual Studio 14.0'
                     r'\VC\vcvarsall.bat')
        assert isfile(vcvarsall)

        with open(join(recipe_dir, 'bld.bat')) as fi:
            data = fi.read()
        with open(join(src_dir, 'bld.bat'), 'w') as fo:
            # more debuggable with echo on
            fo.write('@echo on\n')
            for kv in env.items():
                fo.write('set %s=%s\n' % kv)
            fo.write('call "%s" amd64\n' % vcvarsall)
            fo.write(":: --- end generated header ---\n")
            fo.write(data)

        cmd = [os.environ['COMSPEC'], '/c', 'bld.bat']
        check_call(cmd, cwd=src_dir)
    else:
        cmd = ['/bin/bash', '-x', '-e', join(recipe_dir, 'build.sh')]
        check_call(cmd, env=env, cwd=src_dir)


def main():
    from optparse import OptionParser

    p = OptionParser(usage="usage: %prog [options] PACKAGE [PACKAGE ...]",
                     description="build a package")

    p.add_option("--version",
                 action = "store_true",
                 help = "pint version and exit")

    opts, args = p.parse_args()

    if opts.version:
        from rafe import __version__
        print("rafe: %s" % __version__)
        return

    for arg in args:
        build(join(recipes_dir, arg))


if __name__ == '__main__':
    main()
