from typing import List
from collections import namedtuple
from urllib.parse import urlparse
from dataclasses import dataclass, asdict

import subprocess as sp
import asyncssh
import asyncio
import logging
import shlex
import json
import os

logger = logging.getLogger(__name__)


CmdResult = namedtuple('CmdResult', ['stdout', 'stderr', 'exit_status'])


class Slurm:

    def __init__(self, sbatch='sbatch',  sacct='sacct', python_cmd='python3'):
        self._sbatch_bin = sbatch
        self._sacct_bin = sacct
        self._cmd_runner = CommandRunner(python_cmd=python_cmd)

    def ssh_config(self, url: str, ssh_config='~/.ssh/config', python_cmd=None):
        self._cmd_runner.config_ssh(url, ssh_config, python_cmd)
        return self

    async def _submit(self, *script: str, recovery_file: str = '',wait=False,
                      timeout=None, cwd=None, opts='', tries=1, interval=10):
        """
        Submit Slurm scripts

        :param script: Script files to submit, can be glob patterns.
        Note that if ssh is configured, the script files should be on the remote machine.
        :param recovery_file: Recovery file to store the state of the submitted scripts
        Note that if ssh is configured, the recovery file should be on the remote machine.
        :param wait: If True, wait for the job to finish
        :param timeout: Timeout in seconds for waiting
        :param cwd: Working directory
        :param opts: Additional options for sbatch
        """
        # Load recovery state
        state = {}
        if recovery_file:
            try:
                recovery = await self._cmd_runner.text_load(recovery_file, cwd=cwd)
                state = json.loads(recovery)  # type: ignore
            except Exception as e:
                logger.warning('Failed to load recovery file: %s', e)
        logger.info('Recovery state: %s', state)

        scripts = await self._cmd_runner.globs(*script, cwd=cwd)
        for script_file in scripts:
            script_file = os.path.normpath(script_file)
            if script not in state:
                # submit the script
                if '--parsable' not in opts:
                    opts += ' --parsable'
                cmd = f'{self._sbatch_bin} {opts} {script_file}'
                result = await self._cmd_runner.run(cmd, cwd=cwd)


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

    async def text_load(self, path: str, cwd=None):
        return await self.run(f'cat {path}', cwd=cwd)

    async def text_dump(self, path: str, content: str, cwd=None):
        return await self.run(f'echo {shlex.quote(content)} > {path}', cwd=cwd)

    async def globs(self, *path: str, cwd=None) -> List[str]:
        paths = set()
        for p in path:
            result = await self.glob(p, cwd=cwd)
            paths.update(result)
        return list(paths)

    async def glob(self, pattern: str, cwd=None) -> List[str]:
        if not ('*' in pattern or '?' in pattern):
            return [pattern]
        script = shlex.quote(
            f'''from glob import glob; from json import dumps; print(dumps(glob({repr(pattern)})))''')
        cmd = f'{self._python_cmd} -c {script}'
        result = await self.run(cmd, cwd=cwd)
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
