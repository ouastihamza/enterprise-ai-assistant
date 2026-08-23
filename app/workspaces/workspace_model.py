from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class Workspace:
    id: str
    name: str
    company_name: str
    industry: Optional[str] = None
    description: Optional[str] = None
    enabled_modules: List[str] = field(default_factory=list)
    status: str = "active"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)