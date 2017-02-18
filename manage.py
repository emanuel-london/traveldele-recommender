#!/usr/bin/env python
"""Flask management script. Entrypoint for application."""


import os


from flask_migrate import (
    Migrate, MigrateCommand,
)
from flask_script import Manager


from app import (
    create_app, sql, get_app_prefix,
)
from app.utils.commands import (
    CreateAdminCommand, InitDbCommand,
    InstallCommand,
)
import app.utils.context  # @UnusedImport Inject global template variables.


app = create_app(
    os.environ.get('{0}_CONFIG'.format(get_app_prefix()), 'default'))
manager = Manager(app)
manager.add_command('create-admin', CreateAdminCommand)
manager.add_command('db', MigrateCommand)
manager.add_command('do-install', InstallCommand)
manager.add_command('initdb', InitDbCommand)
migrate = Migrate(app, sql)


@manager.command
def test():
    """Run the unit tests."""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


if __name__ == '__main__':
    manager.run()
