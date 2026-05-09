import glob
import os
import sys

class Shell:

    def try_file(self, *files:str):
        """
        Return the first existing file, directory, or matching glob from the given list

        :param files: candidate file, directory, or glob paths
        """
        for path in files:
            if glob.glob(path, recursive=True):
                return path

        print(f"Error: None of the given files or directories exist: {', '.join(files)}", file=sys.stderr)
        sys.exit(1)

    def require_env(self, *env_names:str):
        """
        Check if the required environment variables are set

        :param env_names: list of environment variable names
        """
        missing = []
        for env_name in env_names:
            v = os.getenv(env_name)
            if v is None or v.strip() == '':
                missing.append(env_name)
            else:
                print(f"{env_name}={v}")

        if missing:
            print(f"Error: Missing required environment variables: {', '.join(missing)}", file=sys.stderr)
            sys.exit(1)
