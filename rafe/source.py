import os
import sys
from subprocess import check_call
from os.path import basename, join, isdir, isfile
from urllib.parse import urlparse

from rafe.utils import download, hashsum_file, rm_rf, tar_xf
from rafe.config import work_dir, src_cache
from rafe.metadata import render_recipe


def get_dir():
    lst = [fn for fn in os.listdir(work_dir) if not fn.startswith('.')]
    if len(lst) == 1:
        dir_path = join(work_dir, lst[0])
        if isdir(dir_path):
            return dir_path
    return work_dir


def download_to_cache(source):
    if not isdir(src_cache):
        os.makedirs(src_cache)

    fn = basename(urlparse(source['url']).path)
    md5 = source.get('md5')
    path = join(src_cache, fn)

    if not isfile(path):
        download(source['url'], path, md5)

    assert isfile(path)
    for ht in 'md5', 'sha1', 'sha256':
        if ht in source and hashsum_file(path, ht) != source[ht]:
            raise Exception("%s mismatch: %r" % (ht.upper(), source))
    return path


def unpack(source):
    src_path = download_to_cache(source)

    os.makedirs(work_dir)
    if src_path.endswith(('.tar.gz', '.tar.bz2', '.tgz', '.tar.xz', '.tar')):
        tar_xf(src_path, work_dir)
    else:
        raise Exception("not a vaild source")


def apply_patch(src_dir, path):
    print('Applying patch: %r' % path)
    assert isfile(path), path
    args = ['-p0', '-i', path]
    check_call(['patch',] + args, cwd=src_dir)
    if sys.platform == 'win32' and os.path.exists(args[-1]):
        os.remove(args[-1])  # clean up .patch_unix file


def provide(recipe_dir):
    """
    given the metadata:
      - download (if necessary)
      - unpack
      - apply patches (if any)
    """
    meta = render_recipe(recipe_dir)
    source = meta.get('source', {})
    rm_rf(work_dir)
    if 'url' in source:
        unpack(source)
    else: # no source
        os.makedirs(work_dir)

    if 'patch' in source:
        src_dir = get_dir()
        for patch in source.get('patches', []):
            apply_patch(src_dir, recipe_dir, patch)


if __name__ == '__main__':
    from rafe.config import recipes_dir
    provide(join(recipes_dir, 'bitarray'))
