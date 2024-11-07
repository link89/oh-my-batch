
class Batch:

    def __init__(self):
        pass

    def add_work_dirs(self, *dir: str):
        """
        Add working directories

        """
        return self
    
    def on_setup(self, script: str):
        """
        Add a setup script

        """
        return self
    
    def on_teardown(self, script: str):
        """
        Add a teardown script

        """
        return self
    
    def set_concurrency(self, n: int):
        """
        Set concurrency

        """
        return self
    
    def add_command(self, cmd: str):
        """
        Add a command

        """
        return self
    
    def make_scripts(self):
        """
        Make scripts

        """
        return self

    