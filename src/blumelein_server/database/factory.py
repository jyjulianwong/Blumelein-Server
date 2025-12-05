"""Database factory for creating and managing database adapters."""

from ..config import settings
from .adapter import DatabaseAdapter
from .firestore_adapter import FirestoreAdapter


# Global database adapter instance
_db_adapter: DatabaseAdapter | None = None


def get_database_adapter() -> DatabaseAdapter:
    """
    Get the configured database adapter instance.
    
    Returns:
        The global database adapter instance
        
    Raises:
        RuntimeError: If database has not been initialized
    """
    if _db_adapter is None:
        raise RuntimeError(
            "Database not initialized. Call initialize_database() first."
        )
    return _db_adapter


async def initialize_database() -> DatabaseAdapter:
    """
    Initialize the database adapter based on configuration.
    
    Returns:
        The initialized database adapter
    """
    global _db_adapter
    
    if settings.database_type == "firestore":
        _db_adapter = FirestoreAdapter(
            project_id=settings.google_cloud_project or None
        )
    else:
        raise ValueError(f"Unknown database type: {settings.database_type}")
    
    await _db_adapter.initialize()
    return _db_adapter


async def close_database() -> None:
    """Close the database connection and cleanup resources."""
    global _db_adapter
    
    if _db_adapter:
        await _db_adapter.close()
        _db_adapter = None

