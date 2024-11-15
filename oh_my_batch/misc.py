from .assets import get_asset

class Misc:

    def export_shell_func(self):
        """
        Export shell functions for batch scripts

        For example, you can load them to you shell environment with the following command:
            omb misc export-shell-func > omb-func.sh && source omb-func.sh
        """
        shell_func = get_asset('functions.sh')
        with open(shell_func, 'r', encoding='utf-8') as f:
            print(f.read())
