#!/usr/bin/env python3

"""
Find files that look like test result reports and upload them to wacklig.pipifein.dev
"""

import os
import argparse
import tarfile
import tempfile
from subprocess import check_output
from urllib.request import urlopen
from urllib.parse import urlencode
from glob import glob


def search_env(*options):
    for option in options:
        value = os.environ.get(option)
        if value:
            return value


def jenkins_env():
    return {
        'service': 'jenkins',
        'branch': search_env('ghprbSourceBranch', 'GIT_BRANCH', 'BRANCH_NAME'),
        'commit': search_env('ghprbActualCommit', 'GIT_COMMIT'),
        'pr': search_env('ghprbPullId', 'CHANGE_ID'),
        'build': os.environ.get('BUILD_NUMBER'),
    }


def get_ci_info():
    if os.environ.get('JENKINS_URL'):
        return jenkins_env()

    return {
        'service': 'local',
        'branch': check_output(
            ['git', 'branch', '--show-current'],
            universal_newlines=True
        ).strip(),
        'commit': check_output(
            ['git', 'rev-parse', 'HEAD'],
            universal_newlines=True
        ).strip(),
    }


def find_test_files():
    return glob('**/test-results/test/*.xml', recursive=True)


def upload_files(token, server, ci_info, files):
    if not files:
        raise SystemExit('No test files found')
    ci_info['token'] = token
    with tempfile.NamedTemporaryFile() as fd:
        with tarfile.open(fd.name, 'w:gz') as tar:
            for filename in files:
                tar.add(filename)
        ci_info = {k: v for (k, v) in ci_info.items() if v}
        params = ci_info and '?' + urlencode(ci_info) or ''
        result = urlopen(server + '/api/v1/upload' + params, data=fd)
        print(result.read().decode('utf-8'))


def main():
    parser = argparse.ArgumentParser('wacklig')
    parser.add_argument('--server', type=str, default='https://wacklig.pipifein.dev')
    parser.add_argument('--token', type=str, required=True)
    args = parser.parse_args()
    ci_info = get_ci_info()
    files = find_test_files()
    upload_files(args.token, args.server, ci_info, files)
    print(f'Uploaded {len(files)} files')


if __name__ == "__main__":
    main()
