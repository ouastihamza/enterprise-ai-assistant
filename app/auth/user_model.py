from dataclasses import dataclass, field
from datetime import datetime
from typing import List
from uuid import uuid4


@dataclass
class User:
    """
    Represents a platform user.

    This model is shared across every AI module in the
    AI Solutions Platform.
    """

    email: str

    full_name: str

    password_hash: str

    id: str = field(
        default_factory=lambda: str(uuid4())
    )

    workspace_ids: List[str] = field(
        default_factory=list
    )

    is_active: bool = True

    is_superuser: bool = False

    created_at: datetime = field(
        default_factory=datetime.now
    )

    updated_at: datetime = field(
        default_factory=datetime.now
    )