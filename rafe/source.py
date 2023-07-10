import os
import pathlib
import sys
import git
import shutil
from subprocess import check_call
from os.path import basename, join, isdir, isfile
from urllib.parse import urlparse

from rafe.logger import logger
from rafe.utils import download, hashsum_file, rm_rf, tar_xf
from rafe.config import work_dir, src_cache
from rafe.metadata import render_recipe


def get_dir(package):
    lst = list(pathlib.Path(work_dir).glob(f'{package["name"]}-{package["version"]}*'))
    if len(lst) == 1:
        dir_path = join(work_dir, lst[0])
        if isdir(dir_path):
            return dir_path
    return work_dir


def download_to_cache(source, package):
    if not isdir(src_cache):
        logger.info(f"CREATE | Directory at: {src_cache}")
        os.makedirs(src_cache)

    filename = basename(urlparse(source["url"]).path)

    if filename.endswith((".tar.gz", ".tar.bz2", ".tgz", ".tar.xz", ".tar")):
        md5 = source.get("md5")
        path = join(src_cache, filename)

        if not isfile(path):
            download(source["url"], path, md5)

        assert isfile(path)

        for ht in "md5", "sha1", "sha256":
            if ht in source and hashsum_file(path, ht) != source[ht]:
                raise Exception("%s mismatch: %r" % (ht.upper(), source))

    else:
        path = src_cache + f'/{package["name"]}-{package["version"]}-{source["sha"]}/'
        if pathlib.Path(path).exists():
            logger.info(f"Source exists at: {path}")
            return path

        logger.info(f"CLONE | Repo: {source['url']} -> {path}")
        sha = source.get("sha")

        branch = source.get("branch")
        if branch is None:
            branch = "main"

        repo = git.Repo.clone_from(source["url"], path, branch=branch)
        repo.commit(rev=sha)

    return path


def unpack(source, package):
    src_path = download_to_cache(source, package)

    if not pathlib.Path(work_dir).exists():
        os.makedirs(work_dir)

    if src_path.endswith((".tar.gz", ".tar.bz2", ".tgz", ".tar.xz", ".tar")):
        logger.info(f"UNPACK | {src_cache} -> {work_dir}")
        tar_xf(src_path, work_dir)

    elif isdir(src_path):
        logger.info(f"MOVE | {src_cache} -> {work_dir}")
        new_work_dir = work_dir + "/" + pathlib.Path(src_path).name.__str__() + "/"
        shutil.move(src_path, new_work_dir)

    return src_path


def apply_patch(src_dir, path):
    logger.info("Applying patch: %r" % path)
    assert isfile(path), path
    args = ["-p0", "-i", path]
    check_call(
        [
            "patch",
        ]
        + args,
        cwd=src_dir,
    )
    if sys.platform == "win32" and os.path.exists(args[-1]):
        os.remove(args[-1])  # clean up .patch_unix file


def provide(recipe_dir):
    """
    given the metadata:
      - download (if necessary)
      - unpack
      - apply patches (if any)
    """
    meta = render_recipe(recipe_dir)
    source = meta.get("source", {})
    package = meta.get("package", {})

    if "url" in source:
        source_path = unpack(source, package)
    else:
        os.makedirs(work_dir)

    if "patch" in source:
        if not os.path.isdir(source_path):
            source_path = get_dir(package)
        for patch in source.get("patches", []):
            apply_patch(source_path, recipe_dir, patch)

    if not os.path.isdir(source_path):
        source_path = get_dir(package)

    return source_path
