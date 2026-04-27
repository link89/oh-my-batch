import os

class Shell:

    def require_env(self, *env_names:str):
        """
        Check if the required environment variables are set

        Args:
            env_names: The names of the required environment variables
        """
        for env_name in env_names:
            v = os.getenv(env_name)
            if v is None or v.strip() == '':
                raise ValueError(f'Environment variable {env_name} is required but not set')
