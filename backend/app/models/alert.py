# Pydantic schemas for alert endpoints

from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional


class AlertResponse(BaseModel):
    """Full alert details."""
    id            : UUID
    machine_id    : UUID
    prediction_id : Optional[UUID]
    level         : str
    title         : str
    message       : str
    root_cause    : Optional[str]
    status        : str
    created_at    : datetime

    # Resolution info
    acknowledged_by : Optional[UUID]
    acknowledged_at : Optional[datetime]
    resolved_at     : Optional[datetime]
    resolution_note : Optional[str]

    class Config:
        from_attributes = True


class AlertAcknowledgeRequest(BaseModel):
    """Request body for PATCH /api/alerts/{id}/acknowledge"""
    note: Optional[str] = None


class AlertResolveRequest(BaseModel):
    """Request body for PATCH /api/alerts/{id}/resolve"""
    resolution_note: Optional[str] = None


class AlertSummary(BaseModel):
    """Alert counts by level — for dashboard header."""
    total_active   : int
    critical_count : int
    high_count     : int
    medium_count   : int
    low_count      : int