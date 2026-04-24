import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import relationship

from backend.infrastructure.database import Base


class ProjectORM(Base):
    __tablename__ = "projects"

    id                = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name              = Column(String, nullable=False)
    gps_lat           = Column(Float, nullable=False)
    gps_lon           = Column(Float, nullable=False)
    hourly_irradiance = Column(JSON, nullable=True)
    created_at        = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    charges = relationship("ChargeORM", back_populates="project", cascade="all, delete")


class ChargeORM(Base):
    __tablename__ = "charges"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id      = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    name            = Column(String, nullable=False)
    max_power_w     = Column(Float, nullable=False)
    real_usage_rate = Column(Float, nullable=False)
    hourly_slots    = Column(JSON, nullable=False, default=list)

    project = relationship("ProjectORM", back_populates="charges")
