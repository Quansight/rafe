import collections
import os
import sys
import hashlib
import shutil
import tarfile
import urllib.request
import subprocess
from os.path import join, isdir, isfile, islink, getmtime, getsize
from contextlib import contextmanager
from bz2 import BZ2Decompressor


def download(url, dst_path, md5=None, verbose=False):
    if verbose:
        print("Downloading %s to %s..." % (url, dst_path))

    with urllib.request.urlopen(url) as resp:
        data = resp.read()

    if md5 and hashlib.md5(data).hexdigest() != md5:
        sys.exit("Error: MD5 mismatch, expected: %s" % md5)
    with open(dst_path, 'wb') as fo:
        fo.write(data)


def chunk_file(path, mode='rb', chunksize=262144):
    """
    read potentially large file in chunks (of 256KB by default) so as not to
    use large amounts of memory
    """
    with open(path, mode) as f:
        while 1:
            chunk = f.read(chunksize)
            if not chunk:
                break
            yield chunk


def bunzip2(bz2path, verbose=False):
    assert bz2path.endswith('.bz2')
    path = bz2path[:-4]
    if verbose:
        print("bunz2ing:", bz2path)
    with open(path, mode='wb') as fo:
        bz2_decomp = BZ2Decompressor()
        for c in chunk_file(bz2path):
            fo.write(bz2_decomp.decompress(c))
    assert isfile(path)


def tar_xf(tarball, dir_path, mode='r:*'):
    if tarball.endswith('.tar.xz'):
        subprocess.check_call(['unxz', '-f', '-k', tarball])
        tarball = tarball[:-3]
    t = tarfile.open(tarball, mode)
    t.extractall(path=dir_path)
    t.close()


def rm_rf(path):
    if islink(path) or isfile(path):
        # Note that we have to check if the destination is a link because
        # exists('/path/to/dead-link') will return False, although
        # islink('/path/to/dead-link') is True.
        os.unlink(path)

    elif isdir(path):
        if sys.platform == 'win32':
            subprocess.check_call(['cmd', '/c', 'rd', '/s', '/q', path])
        else:
            shutil.rmtree(path)


def clean_dir(dir_path):
    for fn in os.listdir(dir_path):
        if fn.endswith(('~', '.pyc')):
            rm_rf(join(dir_path, fn))


def hashsum_file(path, mode='md5'):
    h = hashlib.new(mode)
    for chunk in chunk_file(path):
        h.update(chunk)
    return h.hexdigest()


def md5_file(path):
    return hashsum_file(path, 'md5')


def file_info(path, add_sha256=False):
    res = {'size': getsize(path),
           'md5': md5_file(path),
           'mtime': getmtime(path)}
    if add_sha256:
        res['sha256'] = hashsum_file(path, mode='sha256')
    return res


def possibly_download(url, dst_path, md5, verbose=False):
    "download if necessary"
    if isfile(dst_path) and md5_file(dst_path) == md5:
        return
    download(url, dst_path, md5, verbose=verbose)


def human_bytes(n):
    """
    Return the number of bytes n in more human readable form.
    """
    if n < 1024:
        return '%d' % n
    k = float(n) / 1024
    if k < 1024:
        return '%dK' % round(k)
    m = k / 1024
    if m < 1024:
        return '%.1fM' % m
    g = m / 1024
    return '%.2fG' % g


class memoized(object):
    """Decorator. Caches a function's return value each time it is called.
    If called later with the same arguments, the cached value is returned
    (not reevaluated).
    """
    def __init__(self, func):
        self.func = func
        self.cache = {}
    def __call__(self, *args):
        if not isinstance(args, collections.Hashable):
            # uncacheable. a list, for instance.
            # better to not cache than blow up.
            return self.func(*args)
        if args in self.cache:
            return self.cache[args]
        else:
            value = self.func(*args)
            self.cache[args] = value
            return value


@contextmanager
def safe_write(path, mode='w'):
    # write to a temp file and rename afterwards
    tmp_path = path + ".tmp"

    with open(tmp_path, mode=mode) as fo:
        yield fo

    os.rename(tmp_path, path)


if __name__ == '__main__':
    pass
