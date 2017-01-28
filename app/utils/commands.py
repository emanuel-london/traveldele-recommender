"""Flask-Script commands."""


from flask_migrate import (
    init, migrate, upgrade,
)
from flask_script import Command


from app.utils.models import (
    Role, User,
)


class InitDbCommand(Command):
    """Initialise the database and create tables."""

    def run(self):
        init()
        migrate()
        upgrade()


class CreateAdminCommand(Command):
    """Create the admin user in the database."""

    def run(self):
        Role.insert_roles()
        User.insert_admin_user()


class InstallCommand(Command):
    """Perform installation tasks."""

    def run(self):
        pass
