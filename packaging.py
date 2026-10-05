#!/usr/bin/env python3
"""Independent V2 MAIN-only build/validation, using only tracked inputs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import socket
import subprocess
import tarfile
import tempfile
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parent
TARGETS = {
    'amd64': ('opencode-linux-x64-baseline', 'cli-linux-x64-baseline', 'Advanced Micro Devices X86-64', '/lib64/ld-linux-x86-64.so.2', 'x86_64-linux-gnu'),
    'arm64': ('opencode-linux-arm64', 'cli-linux-arm64', 'AArch64', '/lib/ld-linux-aarch64.so.1', 'aarch64-linux-gnu'),
}
PATHS = ['usr/bin/opencode', 'usr/share/bash-completion/completions/opencode', 'usr/share/licenses/opencode/LICENSE']


def run(args, *, cwd=None, env=None, capture=True):
    result = subprocess.run(list(map(str, args)), cwd=cwd, env=os.environ | (env or {}),
                            check=True, text=True, stdout=subprocess.PIPE if capture else None)
    return result.stdout or ''


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def config(root=ROOT, *, approved=False):
    cfg = json.loads((root / 'release.json').read_text())
    if approved and not cfg['source_approved']:
        raise ValueError('Awaiting parent source GO and independent exact-byte checker; no builds authorized')
    return cfg


def target(arch):
    if arch not in TARGETS:
        raise ValueError('Unsupported architecture: ' + arch)
    return TARGETS[arch]


def prepare_source(source, patchfile, cfg):
    if sha256(patchfile.read_bytes()) != cfg['patch_sha256']:
        raise ValueError('Downstream patch checksum mismatch')
    run(['git', 'init', '-q'], cwd=source)
    run(['git', 'add', '--all', '--force'], cwd=source)
    if run(['git', 'write-tree'], cwd=source).strip() != cfg['upstream_tree']:
        raise ValueError('Source archive upstream tree mismatch')
    run(['git', 'apply', '--index', '--binary', str(patchfile)], cwd=source)
    if run(['git', 'write-tree'], cwd=source).strip() != cfg['source_tree']:
        raise ValueError('Patched source tree mismatch')


def compile_cli(source, arch, cfg):
    build_target, dist, *_ = target(arch)
    if json.loads((source / 'package.json').read_text())['packageManager'] != 'bun@' + cfg['bun']:
        raise ValueError('Unexpected source packageManager; never rewrite the compiler requirement')
    actual = run(['bun', '--version']).strip()
    if actual != cfg['bun']:
        raise ValueError(f"opencode {cfg['version']} requires Bun {cfg['bun']}, got {actual}")
    if os.environ.get('BUN_COMPILE_RELEASE') or os.environ.get('OPENCODE_PTY_BIN'):
        raise ValueError('Do not override the pinned compiler or native PTY asset')
    # Install BOTH architectures' optional native dependencies from the frozen
    # lock. The source build must not subsequently mutate dependencies/lockfile.
    run(['bun', 'install', '--frozen-lockfile', '--ignore-scripts', '--os=*', '--cpu=*'], cwd=source, capture=False)
    run(['bun', 'run', './script/build.ts', '--target=' + build_target, '--skip-install'],
        cwd=source / 'packages/cli', env={'OPENCODE_VERSION': cfg['version'], 'OPENCODE_CHANNEL': 'latest',
                                       'SOURCE_DATE_EPOCH': str(cfg['source_epoch'])}, capture=False)
    app = source / 'packages/app/dist'
    if not (app / 'index.html').is_file() or not list((app / '_assets').glob('*.js')):
        raise ValueError('Native build omitted bundled UI output')
    binary = source / 'packages/cli/dist' / dist / 'bin/opencode'
    check_elf(binary, arch)
    return binary


def runner(arch):
    target(arch)
    host = {'x86_64': 'amd64', 'aarch64': 'arm64', 'arm64': 'arm64'}.get(platform.machine())
    if host == arch:
        return []
    if host == 'amd64' and arch == 'arm64':
        return ['qemu-aarch64-static', '-L', '/']
    raise ValueError(f'Cannot execute {arch} binary on {host}')


def check_elf(binary, arch):
    _, _, machine, interpreter, _ = target(arch)
    header = run(['readelf', '-h', str(binary)])
    program = run(['readelf', '-l', str(binary)])
    if not re.search(r'Class:\s+ELF64\b', header):
        raise ValueError('Unexpected ELF class')
    if not re.search(r'Machine:\s+' + re.escape(machine) + r'\s*$', header, re.M):
        raise ValueError('Unexpected ELF machine for ' + arch)
    if '[Requesting program interpreter: ' + interpreter + ']' not in program:
        raise ValueError('Unexpected ELF interpreter for ' + arch)


def completions(binary, arch):
    result = {}
    for shell in ['bash', 'zsh']:
        text = run(runner(arch) + [str(binary), '--completions', shell], env={'SHELL': '/bin/' + shell})
        if not text.strip():
            raise ValueError('empty ' + shell + ' completion output')
        result[shell] = text
    return result


def ui_asset(html, content_type):
    match = re.search(r'<script\b[^>]*\bsrc=["\'](/_assets/[^"\']+\.js)["\']', html)
    if 'text/html' not in content_type or not re.search(r'<html\b', html, re.I) or not match:
        raise ValueError('Missing bundled UI HTML or local JavaScript asset')
    return match.group(1)


def smoke_ui(binary, arch):
    # Direct, isolated foreground serve. Never service/start/systemctl and never
    # the user's config, storage or installed server. Called offline by wrappers.
    with tempfile.TemporaryDirectory(prefix='v2-ui-smoke-', dir='/tmp') as temporary:
        home = Path(temporary)
        with socket.socket() as listener:
            listener.bind(('127.0.0.1', 0))
            port = listener.getsockname()[1]
        env = {key: value for key, value in os.environ.items() if not key.startswith('OPENCODE_')}
        env.update({'HOME': str(home), 'XDG_CONFIG_HOME': str(home / 'config'),
                    'XDG_DATA_HOME': str(home / 'data'), 'XDG_STATE_HOME': str(home / 'state'),
                    'XDG_CACHE_HOME': str(home / 'cache'), 'SHELL': '/bin/bash',
                    'OPENCODE_CONFIG_DIR': str(home / 'config'),
                    'OPENCODE_DISABLE_MODELS_FETCH': '1', 'OPENCODE_CONFIG_PROJECT_DISABLE': '1'})
        with (home / 'serve.log').open('w+') as log:
            process = subprocess.Popen(runner(arch) + [str(binary), 'serve', '--hostname', '127.0.0.1', '--port', str(port)],
                                       cwd=home, env=env, stdout=log, stderr=log)
            try:
                deadline = time.monotonic() + 120
                url = f'http://127.0.0.1:{port}'
                while True:
                    if process.poll() is not None:
                        raise ValueError('Isolated serve exited: ' + (home / 'serve.log').read_text())
                    try:
                        with urllib.request.urlopen(url + '/', timeout=2) as response:
                            asset = ui_asset(response.read().decode(), response.headers.get('Content-Type', ''))
                        break
                    except (urllib.error.URLError, TimeoutError):
                        if time.monotonic() >= deadline:
                            raise ValueError('Bundled UI readiness timeout: ' + (home / 'serve.log').read_text())
                        time.sleep(0.2)
                with urllib.request.urlopen(url + asset, timeout=10) as response:
                    if not response.read() or 'javascript' not in response.headers.get('Content-Type', ''):
                        raise ValueError('Missing bundled UI JavaScript response')
            finally:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()


def smoke(binary, arch, version):
    check_elf(binary, arch)
    actual = run(runner(arch) + [str(binary), '--version'], env={'SHELL': '/bin/bash'}).strip()
    if actual != version.split('-')[0]:
        raise ValueError('Binary version mismatch: ' + actual)
    if not run(runner(arch) + [str(binary), '--help'], env={'SHELL': '/bin/bash'}).strip():
        raise ValueError('Empty CLI help')
    completions(binary, arch)
    smoke_ui(binary, arch)


def stage_cli(source, binary, destination, arch, zshdir):
    files = {
        'usr/bin/opencode': (binary, 0o755),
        'usr/share/licenses/opencode/LICENSE': (source / 'LICENSE', 0o644),
    }
    for relative, (path, mode) in files.items():
        output = destination / relative
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, output)
        output.chmod(mode)
    for shell, text in completions(binary, arch).items():
        relative = 'usr/share/bash-completion/completions/opencode' if shell == 'bash' else zshdir + '/_opencode'
        output = destination / relative
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text)
        output.chmod(0o644)
    check_main_only(destination)


def check_main_only(directory):
    if any((directory / p).exists() for p in ['usr/bin/ocd', 'usr/bin/opencode-daemon']):
        raise ValueError('Forbidden MAIN-only payload: legacy wrapper')
    if any(p.is_file() or p.is_symlink() for p in (directory / 'usr/lib/systemd').rglob('*')):
        raise ValueError('Forbidden MAIN-only payload: service unit')


def shlibdeps(binary, arch, work):
    multiarch = target(arch)[4]
    directory = work / ('shlibdeps-' + arch)
    (directory / 'debian').mkdir(parents=True, exist_ok=True)
    (directory / 'debian/control').write_text('Source: opencode\nPackage: opencode\nArchitecture: ' + arch + '\n')
    text = run(['dpkg-shlibdeps', '-O', '-Tsubstvars', '-l/usr/lib/' + multiarch,
                '-l/lib/' + multiarch, '-e' + str(binary)], cwd=directory,
               env={'DEB_HOST_ARCH': arch, 'DEB_HOST_GNU_TYPE': multiarch, 'DEB_HOST_MULTIARCH': multiarch})
    for line in text.splitlines():
        if line.startswith('shlibs:Depends=') and line.removeprefix('shlibs:Depends='):
            return line.removeprefix('shlibs:Depends=')
    raise ValueError('dpkg-shlibdeps returned no shlibs:Depends')


def source_archive(cfg, work):
    archive = work / 'upstream.tar.gz'
    cached = os.environ.get('SOURCE_ARCHIVE')
    if cached:
        shutil.copyfile(cached, archive)
    else:
        with urllib.request.urlopen(cfg['source_url'], timeout=120) as response, archive.open('wb') as output:
            shutil.copyfileobj(response, output)
    if sha256(archive.read_bytes()) != cfg['source_sha256']:
        raise ValueError('Upstream source archive checksum mismatch')
    with tarfile.open(archive) as tar:
        # Only the immutable, SHA256-verified upstream archive is extracted.
        # Use the Python API shared by the Debian and Arch builder versions.
        tar.extractall(work / 'source')
    return work / 'source' / ('opencode-' + cfg['upstream_commit'])


def build_deb(root, arch, out):
    cfg = config(root, approved=True)
    target(arch)
    version = f"{cfg['version']}-{cfg['revision']}"
    out.mkdir(parents=True, exist_ok=True)
    package = out / f'opencode_{version}_{arch}.deb'
    if package.exists():
        raise ValueError('Refusing to reuse existing output: ' + str(package))
    with tempfile.TemporaryDirectory(prefix='opencode-v2-build-', dir='/tmp') as temporary:
        work = Path(temporary)
        source = source_archive(cfg, work)
        prepare_source(source, root / f"downstream-{cfg['version']}.patch", cfg)
        binary = compile_cli(source, arch, cfg)
        package_root = work / 'pkg'
        stage_cli(source, binary, package_root, arch, 'usr/share/zsh/vendor-completions')
        control = package_root / 'DEBIAN'
        control.mkdir()
        depends = shlibdeps(binary, arch, work) + ', curl, ripgrep, tar'
        size = run(['du', '-sk', str(package_root / 'usr')]).split()[0]
        (control / 'control').write_text(f"Package: opencode\nVersion: {version}\nSection: utils\nPriority: optional\nArchitecture: {arch}\nMaintainer: opencode downstream maintainers <noreply@example.invalid>\nInstalled-Size: {size}\nDepends: {depends}\nHomepage: https://github.com/anomalyco/opencode\nDescription: The open source coding agent\n V2 native CLI with bundled web UI.\n")
        sums = []
        for path in sorted((package_root / 'usr').rglob('*')):
            if path.is_file():
                sums.append(hashlib.md5(path.read_bytes()).hexdigest() + '  ' + str(path.relative_to(package_root)))
        (control / 'md5sums').write_text('\n'.join(sums) + '\n')
        run(['dpkg-deb', '--build', '--root-owner-group', str(package_root), str(package)],
            env={'SOURCE_DATE_EPOCH': str(cfg['source_epoch'])}, capture=False)
        validate_deb(package, version, arch)
    print('Built and validated ' + str(package))


def verify_paths(directory, zshdir):
    for relative in PATHS + [zshdir + '/_opencode']:
        path = directory / relative
        if not path.is_file() or not path.stat().st_size:
            raise ValueError('Missing/empty package path ' + relative)
    if not os.access(directory / 'usr/bin/opencode', os.X_OK):
        raise ValueError('Package CLI is not executable')
    check_main_only(directory)


def validate_deb(package, version, arch):
    target(arch)
    for field, expected in [('Package', 'opencode'), ('Version', version), ('Architecture', arch)]:
        if run(['dpkg-deb', '-f', str(package), field]).strip() != expected:
            raise ValueError('Unexpected Debian ' + field)
    if not run(['dpkg-deb', '-f', str(package), 'Depends']).strip():
        raise ValueError('Missing Debian Depends')
    run(['dpkg-deb', '-I', str(package)], capture=False)
    run(['dpkg-deb', '-c', str(package)], capture=False)
    with tempfile.TemporaryDirectory(dir='/tmp') as temporary:
        directory = Path(temporary)
        run(['dpkg-deb', '-x', str(package), str(directory)])
        verify_paths(directory, 'usr/share/zsh/vendor-completions')
        smoke(directory / 'usr/bin/opencode', arch, version)
    print(f'Validated opencode {version} ({arch}, ELF/version/help/completions/bundled UI)')


def validate_arch(package, version):
    run(['pacman', '-Qip', str(package)], capture=False)
    if run(['pacman', '-Qp', str(package)]).strip() != 'opencode ' + version:
        raise ValueError('Unexpected Arch name/version')
    info = run(['bsdtar', '-xOf', str(package), '.PKGINFO'])
    if not re.search(r'^arch = x86_64$', info, re.M):
        raise ValueError('Unexpected Arch architecture')
    with tempfile.TemporaryDirectory(dir='/tmp') as temporary:
        directory = Path(temporary)
        run(['bsdtar', '-xf', str(package), '-C', str(directory)])
        verify_paths(directory, 'usr/share/zsh/site-functions')
        smoke(directory / 'usr/bin/opencode', 'amd64', version)
    print(f'Validated opencode {version} (Arch x86_64, bundled UI)')


def docker_build(root, kind, arch, out):
    cfg = config(root, approved=True)
    target(arch)
    version = f"{cfg['version']}-{cfg['revision']}"
    filename = f'opencode_{version}_{arch}.deb' if kind == 'debian' else f'opencode-{version}-x86_64.pkg.tar.zst'
    out = out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    if (out / filename).exists():
        raise ValueError('Refusing to reuse existing output: ' + filename)
    image = f'opencode-v2-{kind}:{version}-{arch}'
    container = f'opencode-v2-{kind}-{arch}-{os.getpid()}'
    dockerfile = 'Dockerfile.debian' if kind == 'debian' else 'Dockerfile.makepkg'
    args = ['docker', 'build', '--platform', 'linux/amd64', '--file', str(root / dockerfile), '--tag', image]
    if kind == 'debian':
        args += ['--build-arg', 'DEB_ARCH=' + arch]
    run(args + [str(root)], capture=False)
    run(['docker', 'create', '--platform', 'linux/amd64', '--name', container, image])
    try:
        run(['docker', 'start', '--attach', container], capture=False)
        if run(['docker', 'inspect', '--format', '{{.State.ExitCode}}', container]).strip() != '0':
            raise ValueError('Build container failed')
        directory = '/out' if kind == 'debian' else '/build'
        run(['docker', 'cp', container + ':' + directory + '/' + filename, str(out / filename)])
        helper = '/pkg/validate-deb' if kind == 'debian' else '/build/validate-arch'
        args = ['docker', 'run', '--rm', '--platform', 'linux/amd64', '--network', 'none', '--volume', str(out) + ':/export:ro',
                '--entrypoint', helper, image, '/export/' + filename, version]
        if kind == 'debian':
            args += [arch]
        run(args, capture=False)
    finally:
        run(['docker', 'rm', '-f', container])


def ubuntu(package, version):
    if not re.search(r'^ID=ubuntu$', Path('/etc/os-release').read_text(), re.M) or not re.search(r'^VERSION_ID="24\.04"$', Path('/etc/os-release').read_text(), re.M):
        raise ValueError('Validator must be Ubuntu 24.04')
    if run(['dpkg', '--print-architecture']).strip() != 'amd64' or 'arm64' not in run(['dpkg', '--print-foreign-architectures']).split():
        raise ValueError('Validator requires amd64 builder with arm64 userspace')
    validate_deb(package, version, 'arm64')
    run(['dpkg', '--unpack', str(package)], capture=False)
    run(['dpkg', '--configure', 'opencode:arm64'], capture=False)
    for field, expected in [('${db:Status-Status}', 'installed'), ('${Architecture}', 'arm64'), ('${Version}', version)]:
        if run(['dpkg-query', '-W', '-f=' + field, 'opencode:arm64']).strip() != expected:
            raise ValueError('Ubuntu installed metadata mismatch')
    smoke(Path('/usr/bin/opencode'), 'arm64', version)
    print('Validated Ubuntu 24.04 arm64 userspace with direct qemu-aarch64-static (not hardware DGX validation)')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    for name, fields in {
        'build-deb': ['arch'], 'docker-debian': ['arch'], 'docker-arch': [],
        'prepare': ['source', 'patch'], 'compile': ['source', 'arch'],
        'stage': ['source', 'binary', 'destination', 'arch', 'zshdir'],
        'smoke': ['binary', 'arch', 'version'], 'validate-deb': ['package', 'version', 'arch'],
        'validate-arch': ['package', 'version'], 'ubuntu': ['package', 'version'],
        'docker-ubuntu': ['package', 'version'],
    }.items():
        command = commands.add_parser(name)
        for field in fields:
            command.add_argument(field)
    args = parser.parse_args()
    out = Path(os.environ.get('OUT_DIR', ROOT / 'dist'))
    if args.command == 'build-deb':
        build_deb(ROOT, args.arch, out)
    elif args.command == 'docker-debian':
        for arch in ['amd64', 'arm64'] if args.arch == 'all' else [args.arch]:
            docker_build(ROOT, 'debian', arch, out)
    elif args.command == 'docker-arch':
        docker_build(ROOT, 'arch', 'amd64', out)
    elif args.command in ['prepare', 'compile', 'stage']:
        cfg = config(approved=True)
        if args.command == 'prepare':
            prepare_source(Path(args.source), Path(args.patch), cfg)
        elif args.command == 'compile':
            compile_cli(Path(args.source), args.arch, cfg)
        else:
            stage_cli(Path(args.source), Path(args.binary), Path(args.destination), args.arch, args.zshdir)
    elif args.command == 'smoke':
        smoke(Path(args.binary), args.arch, args.version)
    elif args.command == 'validate-deb':
        validate_deb(Path(args.package), args.version, args.arch)
    elif args.command == 'validate-arch':
        validate_arch(Path(args.package), args.version)
    elif args.command == 'ubuntu':
        ubuntu(Path(args.package), args.version)
    else:
        image = 'opencode-v2-ubuntu-validator:24.04'
        package = Path(args.package).resolve()
        if not package.is_file():
            raise ValueError('Missing arm64 package')
        run(['docker', 'build', '--platform', 'linux/amd64', '--file', str(ROOT / 'Dockerfile.ubuntu-arm64-validate'), '--tag', image, str(ROOT)], capture=False)
        run(['docker', 'run', '--rm', '--platform', 'linux/amd64', '--network', 'none', '--volume', str(package.parent) + ':/artifacts:ro', image,
             '/artifacts/' + package.name, args.version], capture=False)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, subprocess.CalledProcessError) as error:
        raise SystemExit(str(error))
