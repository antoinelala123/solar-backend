from sqlalchemy import Column, String, Float, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
from backend.infrastructure.database import Base
from datetime import datetime, timezone
import uuid

class Project(Base):
    __tablename__ = "projects"

    id                  = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name                = Column(String, nullable=False)
    gps_lat             = Column(Float, nullable=False)
    gps_lon             = Column(Float, nullable=False)
    hourly_irradiance   = Column(JSON, nullable=True)  # liste de 24 valeurs W/m², rempli après appel PVGIS
    created_at          = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    charges             = relationship("Charge", back_populates="project", cascade="all, delete")


class Charge(Base):
    __tablename__ = "charges"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id      = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    name            = Column(String, nullable=False)
    max_power_w     = Column(Float, nullable=False)
    real_usage_rate = Column(Float, nullable=False)  # 0.0 → 1.0
    hourly_slots    = Column(JSON, nullable=False, default=list)

    project         = relationship("Project", back_populates="charges")