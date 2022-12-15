import re
from os.path import isfile, join

import yaml


def ns_cfg(cfg):
    plat = cfg['plat']
    return dict(
        mkl = bool(cfg['MKL']),
        debug = bool(cfg['DEBUG']),
        linux = plat.startswith('linux-'),
        win = plat.startswith('win-'),
        win32 = bool(plat == 'win-32'),
        win64 = bool(plat == 'win-64'),
        x86 = plat.endswith(('-32', '-64')),
        x86_64 = plat.endswith('-64'),
    )


sel_pat = re.compile(r'(.+?)\s*\[(.+)\]$')
def select_lines(data, namespace):
    lines = []
    for line in data.splitlines():
        line = line.rstrip()
        m = sel_pat.match(line)
        if m:
            cond = m.group(2)
            if eval(cond, namespace, {}):
                lines.append(m.group(1))
            continue
        lines.append(line)
    return '\n'.join(lines) + '\n'


def yamlize(data):
    res = yaml.safe_load(data)
    # ensure the result is a dict
    if res is None:
        res = {}
    return res


def parse(data, cfg):
    if cfg is not None:
        data = select_lines(data, ns_cfg(cfg))
    # ensure we create new object, because yamlize is memoized
    res = yamlize(data)

    # ensure those are lists
    for fieldname in ('source/patches',
                      'build/entry_points',
                      'test/commands', 'test/imports'):
        section, key = fieldname.split('/')
        if res.get(section) is None:
            res[section] = {}
        if res[section].get(key, None) is None:
            res[section][key] = []
    # ensure those are strings
    for fieldname in ('source/md5', ):
        section, key = fieldname.split('/')
        if res.get(section) is None:
            res[section] = {}
        res[section][key] = str(res[section].get(key, ''))

    return res


def render_recipe(recipe_dir, cfg=None):
    path = join(recipe_dir, 'meta.yaml')
    if not isfile(path):
        return None
    data = open(path).read()
    meta = parse(data, cfg)
    return meta


if __name__ == '__main__':
    from pprint import pprint
    pprint(render_recipe('../examples/bitarray'))
