from backend.domain.entities import Charge, HourlySlot, Project
from backend.infrastructure.models import ChargeORM, ProjectORM


class ChargeMapper:
    @staticmethod
    def to_entity(orm: ChargeORM) -> Charge:
        return Charge(
            id=orm.id,
            project_id=orm.project_id,
            name=orm.name,
            max_power_w=orm.max_power_w,
            real_usage_rate=orm.real_usage_rate,
            hourly_slots=[
                HourlySlot(
                    hour=s["hour"],
                    state=s["state"],
                    custom_value_w=s.get("custom_value_w"),
                )
                for s in (orm.hourly_slots or [])
            ],
        )


class ProjectMapper:
    @staticmethod
    def to_entity(orm: ProjectORM) -> Project:
        return Project(
            id=orm.id,
            name=orm.name,
            gps_lat=orm.gps_lat,
            gps_lon=orm.gps_lon,
            created_at=orm.created_at,
            hourly_irradiance=orm.hourly_irradiance,
            charges=[ChargeMapper.to_entity(c) for c in orm.charges],
        )
