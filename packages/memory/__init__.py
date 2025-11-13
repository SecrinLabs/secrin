from .memory import Memory

# Optional singleton (very useful across the app)
memory = Memory()

__all__ = ["Memory", "memory"]
