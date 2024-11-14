from collections import namedtuple
from urllib.parse import urlparse
import subprocess as sp
import asyncssh
import asyncio
import shlex
import glob
import json



CmdResult = namedtuple('CmdResult', ['stdout', 'stderr', 'exit_status'])


class Slurm:

    def __init__(self, sbatch='sbatch', squeue='squeue', sacct='sacct',
                 python_cmd='python3'):

        self._sbatch_bin = sbatch
        self._squeue_bin = squeue
        self._sacct_bin = sacct
        self._cmd_runner = CommandRunner(python_cmd=python_cmd)

    def ssh_config(self, url: str, ssh_config='~/.ssh/config', python_cmd=None):
        self._cmd_runner.config_ssh(url, ssh_config, python_cmd)
        return self

    def submit(self, *script: str, recovery_file: str, wait=False, timeout=None):

        ...


class CommandRunner:

    def __init__(self, ssh_config=None, python_cmd='python3'):
        self._ssh_config = ssh_config
        self._ssh_connection = None
        self._cwd = None
        self._python_cmd = python_cmd

    def config_ssh(self, url: str, ssh_config='~/.ssh/config', python_cmd=None):
        url_obj = urlparse(url)
        self._cwd = url_obj.path
        self._ssh_config = {
            'host': url_obj.hostname,
            'port': url_obj.port or 22,
            'config': [ssh_config],
        }
        if url_obj.username:
            self._ssh_config['username'] = url_obj.username
        if url_obj.password:
            self._ssh_config['password'] = url_obj.password
        if python_cmd is not None:
            self._python_cmd = python_cmd

    async def ssh_connect(self) -> asyncssh.SSHClientConnection:
        assert self._ssh_config is not None, 'ssh config is not set'
        if self._ssh_connection is None:
            self._ssh_connection = await asyncssh.connect(**self._ssh_config)
        return self._ssh_connection

    async def expand_globs(self, *path: str):
        paths = []
        for p in path:
            if '*' in p:
                result = await self.glob(p)
                paths.extend(result)
            else:
                paths.append(p)

    async def glob(self, pattern: str):
        script = shlex.quote(
            f'''from glob import glob; from json import dumps; print(dumps(glob({repr(pattern)})))''')
        cmd = f'{self._python_cmd} -c {script}'
        result = await self.run(cmd)
        return json.loads(result.stdout)

    async def run(self, cmd: str, cwd=None):
        if cwd is None:
            cwd = self._cwd
        if cwd is not None:
            cmd = f'cd {cwd} && {cmd}'

        if self._ssh_config is None:
            cp = sp.run(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
            return CmdResult(stdout=cp.stdout.decode('utf-8'),
                             stderr=cp.stderr.decode('utf-8'),
                             exit_status=cp.returncode)
        else:
            conn = await self.ssh_connect()
            result = await conn.run(cmd)
            return CmdResult(stdout=result.stdout,
                             stderr=result.stderr,
                             exit_status=result.exit_status)
