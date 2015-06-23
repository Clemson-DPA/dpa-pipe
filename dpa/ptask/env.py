
from dpa.env import Env
from dpa.env.vars import DpaVars

class PTaskEnv(Env):

    @classmethod
    def current(cls):

        env = PTaskEnv()
        env.get()
        return env

    def __init__(self):

        super(PTaskEnv, self).__init__()

        # XXX document the accessor names

        # library path
        self.add(
            DpaVars.path(default=DpaVars.path_base().get()),
            name='path'
        )

        self.add(
            DpaVars.ld_library_path(
                default=DpaVars.ld_library_path_base().get()),
            name='ld_library_path'
        )

        self.add(
            DpaVars.python_path(default=DpaVars.python_path_base().get()),
            name='python_path'
        )

        self.add(DpaVars.ptask_spec(), name='ptask_spec')

        self.add(DpaVars.ptask_path(), name='ptask_path')

        self.add(DpaVars.ptask_version(), name='ptask_version')

