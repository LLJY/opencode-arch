#!/usr/bin/env python3
"""Lightweight packaging regressions: command spies stop before compilation.

These tests exercise the real shell entrypoints; they never compile or create
packages, install host dependencies, or start services.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PackagingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='packaging-regression-', dir=ROOT / 'tests')
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        self.bin = self.work / 'bin'
        self.bin.mkdir()
        self.log = self.work / 'calls'
        self.source = self.work / 'source'
        (self.source / 'packages/opencode').mkdir(parents=True)
        self.env = os.environ | {
            'PATH': f'{self.bin}:{os.environ["PATH"]}',
            'CALLS': str(self.log), 'TEST_BUN_VERSION': '1.3.14',
        }
        self.spy('bun', '''printf 'bun %s version=%s\n' "$*" "${OPENCODE_VERSION:-}" >> "$CALLS"
if [ "$1" = --version ]; then printf '%s\n' "$TEST_BUN_VERSION"; exit; fi
if [ "$1" = run ]; then exit 77; fi
''')
        self.spy('patch', 'printf "patch %s\\n" "$*" >> "$CALLS"\n')

    def spy(self, name, body):
        path = self.bin / name
        path.write_text('#!/bin/bash\nset -eu\n' + body)
        path.chmod(0o755)

    def shell(self, text):
        return subprocess.run(['bash', '-c', text], cwd=self.work, env=self.env,
                              text=True, capture_output=True)

    def calls(self):
        return self.log.read_text() if self.log.exists() else ''

    def test_arch_selects_only_explicit_baseline(self):
        result = self.shell(f'source "{ROOT}/PKGBUILD"; pkgbase="{self.source}"; build')
        self.assertEqual(result.returncode, 77, result.stderr)
        self.assertIn('bun run ./script/build.ts --target=linux-x64-baseline --skip-install', self.calls())
        self.assertNotIn('--single', self.calls())
        self.assertNotIn('--baseline ', self.calls())

    def test_arch_rejects_stale_compiler_before_dependency_install(self):
        self.env['TEST_BUN_VERSION'] = '1.4.2'
        result = self.shell(f'source "{ROOT}/PKGBUILD"; pkgbase="{self.source}"; prepare')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('requires Bun 1.3.14', result.stderr)
        self.assertNotIn('bun install', self.calls())
        self.assertNotIn('patch ', self.calls())

    def test_arch_accepts_exact_compiler(self):
        result = self.shell(f'source "{ROOT}/PKGBUILD"; pkgbase="{self.source}"; prepare')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('bun install --frozen-lockfile --ignore-scripts', self.calls())

    def deb(self, arch, version='1.3.14'):
        # Git/patch are spies, not source provenance tests. The canonical patch
        # and real tree reconstruction are checked separately with Git's index.
        self.spy('git', '''if [ "$1" = clone ]; then mkdir -p "${@: -1}/packages/opencode"; exit; fi
printf '%s\n' "$UPSTREAM_COMMIT"
''')
        for command in ['dpkg-deb', 'dpkg-shlibdeps', 'md5sum', 'qemu-aarch64-static']:
            self.spy(command, 'exit 0\n')
        self.spy('dpkg', 'printf "amd64\\n"\n')
        patch = self.work / 'fixture.patch'
        patch.write_text('command-spy fixture; not a source patch\n')
        self.env.update({
            'DEB_ARCH': arch, 'TEST_BUN_VERSION': version,
            'PATCH_FILE': str(patch), 'UPSTREAM_COMMIT': 'test-fixture',
            'WORK_DIR': str(self.work / 'deb-work'), 'OUT_DIR': str(self.work / 'out'),
        })
        return subprocess.run(['bash', str(ROOT / 'build-deb')], cwd=self.work,
                              env=self.env, text=True, capture_output=True)

    def test_debian_amd64_uses_explicit_baseline(self):
        result = self.deb('amd64')
        self.assertEqual(result.returncode, 77, result.stderr)
        self.assertIn('bun run ./script/build.ts --target=linux-x64-baseline --skip-install', self.calls())
        self.assertIn('version=1.18.35', self.calls())

    def test_debian_arm64_keeps_all_target_optional_install(self):
        result = self.deb('arm64')
        self.assertEqual(result.returncode, 77, result.stderr)
        self.assertIn('bun run ./script/build.ts --target=linux-arm64 version=', self.calls())
        self.assertNotIn('--target=linux-arm64 --skip-install', self.calls())

    def test_debian_rejects_stale_compiler(self):
        result = self.deb('amd64', '1.4.2')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('requires Bun 1.3.14', result.stderr)
        self.assertNotIn('bun install', self.calls())
        self.assertNotIn('patch ', self.calls())

    def test_arch_builder_pins_source_compiler(self):
        dockerfile = (ROOT / 'Dockerfile.makepkg').read_text()
        self.assertIn('oven/bun:1.3.14@sha256:e10577f0db68676a7024391c6e5cb4b879ebd17188ab750cf10024a6d700e5c4 AS bun-toolchain', dockerfile)
        self.assertIn('COPY --from=bun-toolchain /usr/local/bin/bun /opt/bun-1.3.14/bin/bun', dockerfile)
        self.assertIn('ENV PATH="/opt/bun-1.3.14/bin:${PATH}"', dockerfile)

    def test_docker_context_consumes_only_current_patch(self):
        ignore = (ROOT / '.dockerignore').read_text().splitlines()
        self.assertIn('downstream-*.patch', ignore)
        self.assertEqual([line for line in ignore if line.startswith('!downstream-')],
                         ['!downstream-1.18.35.patch'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
