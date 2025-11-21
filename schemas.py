"""
Database Schemas for Men's Tration

Each Pydantic model represents a collection in MongoDB.
Collection name is the lowercase of the class name.
"""
from pydantic import BaseModel, Field
from typing import Optional, List

class Cycle(BaseModel):
    """
    Tracks a partner's cycle preferences
    Collection: "cycle"
    """
    partner_name: Optional[str] = Field(None, description="Name of the person whose cycle is tracked")
    cycle_start: str = Field(..., description="Cycle start date in YYYY-MM-DD")
    cycle_length: int = Field(28, ge=21, le=35, description="Average cycle length in days")

class Idea(BaseModel):
    """
    Advice/idea suggestions mapped to a phase
    Collection: "idea"
    """
    phase: str = Field(..., description="One of: period, follicular, ovulation, luteal")
    title: str = Field(..., description="Short title for the idea")
    description: str = Field(..., description="How to show up / what to do")
    tags: Optional[List[str]] = Field(default=None, description="Optional tags like gifts, food, vibe")

class User(BaseModel):
    """
    Example users collection (not used directly in MVP)
    Collection: "user"
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    is_active: bool = Field(True, description="Whether user is active")
