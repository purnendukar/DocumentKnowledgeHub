from .base import Base
from .user import User
from .document import Document

# Import models here to register them with SQLAlchemy
# This helps prevent circular imports
__all__ = ['Base', 'User', 'Document']
