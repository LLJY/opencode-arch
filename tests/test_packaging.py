"""V2 packaging contracts. Spies stop before compilation/package creation.

Protect native target/UI/compiler selection, target execution, dependency
architecture and source GO. No host installs, source edits or service startup.
"""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
CFG = {
    'version': '2.0.22', 'revision': 1, 'bun': '1.4.2',
    'source_approved': False, 'source_epoch': 1790914978,
    'upstream_tree': 'upstream-fixture', 'source_tree': 'candidate-fixture',
}


class Contracts(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('packaging', ROOT / 'packaging.py')
        assert spec is not None and spec.loader is not None
        self.module = importlib.util.module_from_spec(spec)
        self.assertTrue((ROOT / 'packaging.py').exists(), 'V2 helper not implemented')
        spec.loader.exec_module(self.module)
        self.tmp = tempfile.TemporaryDirectory(dir='/tmp')
        self.addCleanup(self.tmp.cleanup)
        self.work = Path(self.tmp.name)
        (self.work / 'packages/cli').mkdir(parents=True)
        (self.work / 'package.json').write_text(json.dumps({'packageManager': 'bun@1.4.2'}))
        self.calls = []

    def command_spy(self, args, **kwargs):
        self.calls.append((args, kwargs))
        if args == ['bun', '--version']:
            return '1.4.2\n'
        if 'build.ts' in ' '.join(map(str, args)):
            raise RuntimeError('STOP_BEFORE_COMPILE')
        return ''

    def test_native_build_targets_and_bundled_ui(self):
        for arch, target in [('amd64', 'opencode-linux-x64-baseline'), ('arm64', 'opencode-linux-arm64')]:
            self.calls.clear()
            with patch.object(self.module, 'run', side_effect=self.command_spy):
                with self.assertRaisesRegex(RuntimeError, 'STOP_BEFORE_COMPILE'):
                    self.module.compile_cli(self.work, arch, CFG)
            commands = [c[0] for c in self.calls]
            self.assertIn(['bun', 'install', '--frozen-lockfile', '--ignore-scripts', '--os=*', '--cpu=*'], commands)
            command, options = self.calls[-1]
            self.assertEqual(command, ['bun', 'run', './script/build.ts', '--target=' + target, '--skip-install'])
            self.assertEqual(options['cwd'], self.work / 'packages/cli')
            self.assertEqual(options['env']['OPENCODE_VERSION'], '2.0.22')
            self.assertEqual(options['env']['OPENCODE_CHANNEL'], 'latest')
            self.assertNotIn('--skip-web-ui', command)
            self.assertNotIn('--single', command)

    def test_wrong_bun_rejected_before_install(self):
        with patch.object(self.module, 'run', return_value='1.4.0\n') as spy:
            with self.assertRaisesRegex(ValueError, 'requires Bun 1.4.2'):
                self.module.compile_cli(self.work, 'amd64', CFG)
            self.assertEqual(spy.call_count, 1)

    def test_wrong_package_manager_is_not_rewritten(self):
        (self.work / 'package.json').write_text('{"packageManager":"bun@1.4.0"}')
        with patch.object(self.module, 'run') as spy:
            with self.assertRaisesRegex(ValueError, 'packageManager'):
                self.module.compile_cli(self.work, 'amd64', CFG)
            spy.assert_not_called()
        self.assertEqual(json.loads((self.work / 'package.json').read_text())['packageManager'], 'bun@1.4.0')

    def test_unknown_architecture_rejected_before_bun(self):
        with patch.object(self.module, 'run') as spy:
            with self.assertRaisesRegex(ValueError, 'architecture'):
                self.module.compile_cli(self.work, 'all', CFG)
            spy.assert_not_called()

    def test_source_go_is_required_before_docker(self):
        (self.work / 'release.json').write_text(json.dumps(CFG))
        with patch.object(self.module, 'run') as spy:
            with self.assertRaisesRegex(ValueError, 'source GO'):
                self.module.docker_build(self.work, 'debian', 'amd64', self.work / 'out')
            spy.assert_not_called()

    def test_source_tree_verified_before_and_after_patch(self):
        cfg = CFG | {'patch_sha256': self.module.sha256(b'patch fixture')}
        patchfile = self.work / 'fixture.patch'
        patchfile.write_bytes(b'patch fixture')
        with patch.object(self.module, 'run', side_effect=['', '', 'upstream-fixture\n', '', 'candidate-fixture\n']) as spy:
            self.module.prepare_source(self.work, patchfile, cfg)
        self.assertIn(['git', 'apply', '--index', '--binary', str(patchfile)], [c.args[0] for c in spy.call_args_list])

    def test_patch_checksum_and_tree_mismatch_stop(self):
        patchfile = self.work / 'fixture.patch'
        patchfile.write_bytes(b'patch fixture')
        with patch.object(self.module, 'run') as spy:
            with self.assertRaisesRegex(ValueError, 'patch checksum'):
                self.module.prepare_source(self.work, patchfile, CFG | {'patch_sha256': 'wrong'})
            spy.assert_not_called()
        with patch.object(self.module, 'run', side_effect=['', '', 'wrong-tree\n']) as spy:
            with self.assertRaisesRegex(ValueError, 'upstream tree'):
                self.module.prepare_source(self.work, patchfile, CFG | {'patch_sha256': self.module.sha256(patchfile.read_bytes())})
            self.assertEqual(spy.call_count, 3)

    def test_arm_execution_uses_direct_qemu(self):
        with patch.object(self.module.platform, 'machine', return_value='x86_64'):
            self.assertEqual(self.module.runner('arm64'), ['qemu-aarch64-static', '-L', '/'])
            self.assertEqual(self.module.runner('amd64'), [])
        with patch.object(self.module.platform, 'machine', return_value='aarch64'):
            self.assertEqual(self.module.runner('arm64'), [])
            with self.assertRaisesRegex(ValueError, 'execute'):
                self.module.runner('amd64')

    def test_completions_explicit_flags_and_no_old_command(self):
        def completion(args, **kwargs):
            self.calls.append((args, kwargs))
            return '# completion fixture\n'
        with patch.object(self.module, 'run', side_effect=completion), patch.object(self.module.platform, 'machine', return_value='x86_64'):
            result = self.module.completions(Path('/fixture/opencode'), 'arm64')
        self.assertEqual(set(result), {'bash', 'zsh'})
        for shell, (args, kwargs) in zip(('bash', 'zsh'), self.calls):
            self.assertEqual(args, ['qemu-aarch64-static', '-L', '/', '/fixture/opencode', '--completions', shell])
            self.assertEqual(kwargs['env']['SHELL'], '/bin/' + shell)

    def test_smoke_accepts_native_cli_version_label(self):
        binary = self.work / 'opencode-version-fixture'
        binary.write_text('#!/bin/sh\ncase "$1" in --version) printf "opencode v2.0.22\\n";; --help) printf "CLI fixture\\n";; esac\n')
        binary.chmod(0o755)
        # Execute the real process boundary; ELF/UI/completions have separate
        # checks and require a compiled release binary rather than this fixture.
        with patch.object(self.module, 'check_elf'), patch.object(self.module, 'completions'), patch.object(self.module, 'smoke_ui'):
            self.module.smoke(binary, 'amd64', '2.0.22-1')

    def test_empty_completion_fails(self):
        with patch.object(self.module, 'run', return_value=''), patch.object(self.module.platform, 'machine', return_value='x86_64'):
            with self.assertRaisesRegex(ValueError, 'empty bash completion'):
                self.module.completions(Path('/fixture/opencode'), 'amd64')

    def test_elf_rejects_mislabeled_x64_as_arm(self):
        with patch.object(self.module, 'run', side_effect=[
            '  Class: ELF64\n  Machine: Advanced Micro Devices X86-64\n',
            ' [Requesting program interpreter: /lib64/ld-linux-x86-64.so.2]\n',
        ]):
            with self.assertRaisesRegex(ValueError, 'ELF machine'):
                self.module.check_elf(Path('/fixture/opencode'), 'arm64')

    def test_elf_interpreter_checked_for_both_targets(self):
        for arch, machine, interpreter in [
            ('amd64', 'Advanced Micro Devices X86-64', '/lib64/ld-linux-x86-64.so.2'),
            ('arm64', 'AArch64', '/lib/ld-linux-aarch64.so.1'),
        ]:
            with patch.object(self.module, 'run', side_effect=[f' Class: ELF64\n Machine: {machine}\n', f'[Requesting program interpreter: {interpreter}]\n']):
                self.module.check_elf(Path('/fixture/opencode'), arch)
            with patch.object(self.module, 'run', side_effect=[f' Class: ELF64\n Machine: {machine}\n', '[Requesting program interpreter: /wrong]\n']):
                with self.assertRaisesRegex(ValueError, 'ELF interpreter'):
                    self.module.check_elf(Path('/fixture/opencode'), arch)

    def test_shlibdeps_target_architecture_and_no_missing_info_bypass(self):
        for arch, multiarch in [('amd64', 'x86_64-linux-gnu'), ('arm64', 'aarch64-linux-gnu')]:
            with patch.object(self.module, 'run', return_value='shlibs:Depends=libc6 (>= 2.34), libstdc++6 (>= 11)\n') as spy:
                result = self.module.shlibdeps(Path('/fixture/opencode'), arch, self.work)
            self.assertIn('libc6 (>= 2.34)', result)
            args = spy.call_args.args[0]
            self.assertIn('-l/usr/lib/' + multiarch, args)
            self.assertIn('-l/lib/' + multiarch, args)
            self.assertNotIn('--ignore-missing-info', args)
            self.assertEqual(spy.call_args.kwargs['env']['DEB_HOST_ARCH'], arch)
            self.assertEqual(spy.call_args.kwargs['env']['DEB_HOST_MULTIARCH'], multiarch)

    def test_no_shlibdeps_output_is_failure(self):
        with patch.object(self.module, 'run', return_value=''):
            with self.assertRaisesRegex(ValueError, 'shlibs:Depends'):
                self.module.shlibdeps(Path('/fixture/opencode'), 'arm64', self.work)

    def test_main_only_payload(self):
        self.module.check_main_only(self.work)
        for path in ['usr/bin/ocd', 'usr/bin/opencode-daemon', 'usr/lib/systemd/user/opencode.service']:
            forbidden = self.work / path
            forbidden.parent.mkdir(parents=True, exist_ok=True)
            forbidden.touch()
            with self.assertRaisesRegex(ValueError, 'MAIN-only'):
                self.module.check_main_only(self.work)
            forbidden.unlink()

    def test_ui_probe_requires_html_and_local_javascript(self):
        html = '<!doctype html><html><script type="module" src="/_assets/index-test.js"></script></html>'
        self.assertEqual(self.module.ui_asset(html, 'text/html'), '/_assets/index-test.js')
        for bad, content_type in [('<html></html>', 'text/html'), (html, 'application/json'), ('{}', 'application/json')]:
            with self.assertRaisesRegex(ValueError, 'bundled UI'):
                self.module.ui_asset(bad, content_type)

    def test_ui_process_is_direct_isolated_offline_and_terminated(self):
        html = MagicMock()
        html.__enter__.return_value.read.return_value = b'<html><script src="/_assets/test.js"></script></html>'
        html.__enter__.return_value.headers = {'Content-Type': 'text/html'}
        javascript = MagicMock()
        javascript.__enter__.return_value.read.return_value = b'// JavaScript response fixture'
        javascript.__enter__.return_value.headers = {'Content-Type': 'text/javascript'}
        process = MagicMock()
        process.poll.return_value = None
        with patch.object(self.module.subprocess, 'Popen', return_value=process) as spawn, \
             patch.object(self.module.urllib.request, 'urlopen', side_effect=[html, javascript]) as fetch, \
             patch.object(self.module.platform, 'machine', return_value='x86_64'), \
             patch.dict(os.environ, {'OPENCODE_CONFIG': '/private/user/config', 'OPENCODE_CONFIG_DIR': '/private/user', 'OPENCODE_PASSWORD': 'private-fixture'}):
            self.module.smoke_ui(Path('/fixture/opencode'), 'arm64')
        args = spawn.call_args.args[0]
        self.assertEqual(args[:5], ['qemu-aarch64-static', '-L', '/', '/fixture/opencode', 'serve'])
        self.assertNotIn('--service', args)
        env = spawn.call_args.kwargs['env']
        self.assertTrue('OPENCODE_CONFIG' not in env, 'user config override must not be inherited')
        self.assertTrue('OPENCODE_PASSWORD' not in env, 'user password must not be inherited')
        self.assertEqual(Path(env['HOME']).parent, Path('/tmp'))
        self.assertEqual(env['OPENCODE_CONFIG_DIR'], env['XDG_CONFIG_HOME'])
        self.assertEqual(env['OPENCODE_DISABLE_MODELS_FETCH'], '1')
        self.assertEqual(env['OPENCODE_CONFIG_PROJECT_DISABLE'], '1')
        self.assertTrue(all(call.args[0].startswith('http://127.0.0.1:') for call in fetch.call_args_list))
        process.terminate.assert_called_once()
        process.wait.assert_called_once()

    def test_cached_pinned_tar_extracts_with_builder_python(self):
        source = self.work / 'opencode-fixture'
        source.mkdir()
        (source / 'LICENSE').write_text('tar fixture, not release source')
        archive = self.work / 'fixture.tar.gz'
        with tarfile.open(archive, 'w:gz') as tar:
            tar.add(source, arcname='opencode-fixture')
        cfg = CFG | {'upstream_commit': 'fixture', 'source_sha256': self.module.sha256(archive.read_bytes())}
        work = self.work / 'extract'
        work.mkdir()
        with patch.dict(os.environ, {'SOURCE_ARCHIVE': str(archive)}):
            result = self.module.source_archive(cfg, work)
        self.assertEqual((result / 'LICENSE').read_text(), 'tar fixture, not release source')

    def test_docker_matrix_exports_only_main_and_validates_offline(self):
        (self.work / 'release.json').write_text(json.dumps(CFG | {'source_approved': True}))
        for kind, arch, filename in [
            ('arch', 'amd64', 'opencode-2.0.22-1-x86_64.pkg.tar.zst'),
            ('debian', 'amd64', 'opencode_2.0.22-1_amd64.deb'),
            ('debian', 'arm64', 'opencode_2.0.22-1_arm64.deb'),
        ]:
            def docker(args, **kwargs):
                return '0\n' if args[:2] == ['docker', 'inspect'] else ''
            with patch.object(self.module, 'run', side_effect=docker) as spy:
                self.module.docker_build(self.work, kind, arch, self.work / 'out')
            commands = [call.args[0] for call in spy.call_args_list]
            copies = [command for command in commands if command[:2] == ['docker', 'cp']]
            self.assertEqual(len(copies), 1)
            self.assertTrue(copies[0][2].endswith('/' + filename))
            validation = [command for command in commands if command[:2] == ['docker', 'run']][0]
            self.assertIn('--network', validation)
            self.assertEqual(validation[validation.index('--network') + 1], 'none')
            self.assertFalse(any('daemon' in ' '.join(command) for command in commands))
            self.assertEqual(commands[-1][:3], ['docker', 'rm', '-f'])

    def test_pending_entrypoints_do_not_reach_docker_or_bun(self):
        (self.work / 'release.json').write_text(json.dumps(CFG))
        (self.work / 'packaging.py').write_bytes((ROOT / 'packaging.py').read_bytes())
        for name, args in [('build-deb', []), ('build-deb-docker', ['amd64']), ('build-makepkg-docker', [])]:
            self.assertTrue((ROOT / name).exists(), name + ' not implemented')
            entry = self.work / name
            entry.write_bytes((ROOT / name).read_bytes())
            result = subprocess.run(['bash', str(entry), *args], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('source GO', result.stderr)


if __name__ == '__main__':
    unittest.main(verbosity=2)
