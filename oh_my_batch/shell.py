import os
import sys

class Shell:

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
