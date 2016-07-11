# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
import os
import os.path
import subprocess
import sys


ENVPATH = 'envs'


def ensureVCTRepository(revision, hgcustom_orig, env_path):
    base = env_path
    reponame = 'version-control-tools'
    if not os.path.isdir(base):
        os.makedirs(base)
    if os.path.isdir(os.path.join(base, reponame, '.hg')):
        rv = subprocess.call(['hg', 'pull', '-r', revision],
                             cwd=os.path.join(base, reponame))
        if rv:
            raise RuntimeError("hg failed to pull hgcustom's %s" % reponame)
    else:
        rv = subprocess.call(['hg', 'clone', '--noupdate', '--pull',
                              '%s/%s' % (hgcustom_orig, reponame)],
                             cwd=base)
        if rv:
            raise RuntimeError('hg failed to clone %s' % reponame)
    rv = subprocess.call(['hg', 'update', '-c', '-r', revision],
                         cwd=os.path.join(base, reponame))
    if rv:
        raise RuntimeError("hg failed to update -c hgcustom's %s" % reponame)


def ensureRepo(leaf, dest, env_path, push_l10n=True):
    base = os.path.join(dest, 'repos')
    if not os.path.isdir(base):
        os.makedirs(base)
    if os.path.isdir(os.path.join(base, leaf)):
        return

    hg = os.path.abspath(os.path.join(env_path, 'hg', 'bin', 'hg'))
    os.makedirs(os.path.join(base, leaf))
    rv = subprocess.call([hg, 'init', leaf], cwd=base)
    if rv:
        raise RuntimeError('Couldnt hg init %s' % leaf)
    tail = '''
[hooks]
pretxnchangegroup.a_singlehead = python:mozhghooks.single_head_per_branch.hook

[extensions]
pushlog = %(env)s/version-control-tools/hgext/pushlog
pushlog-feed = %(env)s/version-control-tools/hgext/pushlog-legacy/pushlog-feed.py
buglink = %(env)s/version-control-tools/hgext/pushlog-legacy/buglink.py
'''
    hgrc = open(os.path.join(base, leaf, '.hg', 'hgrc'), 'a')
    hgrc.write(tail % {'env': os.path.abspath(env_path)})
    hgrc.close()

    rv = subprocess.call([hg, 'clone', leaf,
                          os.path.join('..', 'workdir', leaf)],
                         cwd=base)
    if rv:
        raise RuntimeError('clone for %s failed' % leaf)
    browserdir = os.path.join(dest, 'workdir', leaf, 'browser')
    if leaf.startswith('l10n'):
        # create initial content for l10n
        os.makedirs(browserdir)
        open(os.path.join(browserdir, 'file.properties'),
             'w').write('''k_e_y: %s value
''' % leaf)
    else:
        # create initial content for mozilla
        os.makedirs(os.path.join(browserdir, 'locales', 'en-US'))
        open(os.path.join(browserdir, 'locales', 'en-US', 'file.properties'),
             'w').write('''k_e_y: en-US value
''')
        open(os.path.join(browserdir, 'locales', 'all-locales'),
             'w').write('''ab
de
ja-JP-mac
x-testing
''')
        open(os.path.join(browserdir, 'locales', 'l10n.ini'),
             'w').write('''[general]
depth = ../..
all = browser/locales/all-locales

[compare]
dirs = browser
''')
    rv = subprocess.call([hg, 'add', '.'], cwd=browserdir)
    if rv:
        raise RuntimeError('failed to add initial content')
    rv = subprocess.call([hg, 'ci', '-mInitial commit for %s' % leaf],
                         cwd=browserdir)
    if rv:
        raise RuntimeError('failed to check in initian content to %s' %
                           leaf)
    if leaf.startswith('l10n') and not push_l10n:
        return
    rv = subprocess.call([hg, 'push'], cwd=browserdir)
    if rv:
        raise RuntimeError('failed to push to %s' % leaf)


def createWebDir(dest, env_path):
    content = '''[collections]
repos = repos

[web]
style = gitweb_mozilla
templates = %(env)s/version-control-tools/hgtemplates
'''
    if not os.path.isfile(os.path.join(dest, 'webdir.conf')):
        open(os.path.join(dest, 'webdir.conf'),
             'w').write(content % {'dest': os.path.abspath(dest),
                                   'env': os.path.abspath(env_path)})


def createEnvironment(env_path, hgcustom_orig):
    '''Get version-control-tools and create hg and automation virtualenvs'''
    if not (hgcustom_orig.startswith('http://') or
            hgcustom_orig.startswith('https://')):
        hgcustom_orig = os.path.expanduser(hgcustom_orig)
        hgcustom_orig = os.path.abspath(hgcustom_orig)
    ensureVCTRepository('628aa8deebcc', hgcustom_orig, env_path)
    # pretend that envs/*/bin/activate is good enough to check this
    for env in ('hg', 'automation'):
        if not os.path.isfile(os.path.join(env_path, env, 'bin', 'activate')):
            venv_cmd = ['virtualenv', os.path.join(env_path, env)]
            rv = subprocess.check_call(venv_cmd)
            if rv:
                raise RuntimeError("Failed to create virtualenv %s in %s" %
                                   (env, env_path))
        pip = os.path.join(env_path, env, 'bin', 'pip')
        rv = subprocess.check_call([pip, 'install', '-U', '-r',
                                    os.path.join(env_path, '..',
                                                 'requirements/' +
                                                 env +
                                                 '.txt')])
        if rv:
            raise RuntimeError("Failed to install requirements from " + env_path)


def setupWorkdir(dest, env_path, push_l10n=False):
    '''Set up the actual working directory for our repos'''
    downstreams = (
        'mozilla',
        'l10n/ab',
        'l10n/de',
        'l10n/ja-JP-mac',
        'l10n/x-testing',
    )
    if not os.path.isdir(os.path.join(dest, 'workdir', 'l10n')):
        os.makedirs(os.path.join(dest, 'workdir', 'l10n'))

    for l in downstreams:
        ensureRepo(l, dest, env_path, push_l10n=push_l10n)

    createWebDir(dest, env_path)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("stagedir", help="Directory to use to create the staging environment")
    p.add_argument('-v', dest='verbose', action='store_true')
    p.add_argument('--hgcustom', default='http://hg.mozilla.org/hgcustom/')
    args = p.parse_args()

    dest = args.stagedir
    createEnvironment(ENVPATH, args.hgcustom)
    setupWorkdir(dest, ENVPATH)
    print 'done'
