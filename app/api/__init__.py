# Package initializer for API routers
# This file allows `app.api` to be imported as a package.
from . import users, notes

__all__ = ["users", "notes"]

