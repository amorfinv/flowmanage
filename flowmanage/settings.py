'''FlowManage global configuration module'''
import os
import flowmanage as fm


def init() -> None:
    '''Initialize configuration.'''

    # get config file path
    cfgfile = os.path.join('', 'settings.cfg')

    fm.con.print(f'[magenta]Reading config from {cfgfile}')

    exec(compile(open(cfgfile).read(), cfgfile, 'exec'), globals())

