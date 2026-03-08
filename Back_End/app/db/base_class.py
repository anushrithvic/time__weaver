"""
Compatibility shim: `app.db.base_class` expected by some modules/tests.
Exports `Base` declarative base from `app.db.session`.
"""

from app.db.session import Base

__all__ = ["Base"]
