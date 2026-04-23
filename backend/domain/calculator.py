import math


def _load_at_hour(charge, hour: int) -> float:
    """Consommation réelle en Wh d'une charge à une heure donnée."""
    slot = next((s for s in charge.hourly_slots if s["hour"] == hour), None)
    if slot is None or slot["state"] == "INACTIVE":
        return 0.0
    if slot["state"] == "CUSTOM":
        return slot.get("custom_value_w") or 0.0
    # ACTIVE : puissance nominale × taux d'usage réel
    return charge.max_power_w * charge.real_usage_rate


def _find_min_panels(daily_load_wh: float, daily_solar_per_panel_wh: float) -> int:
    """Plus petit nombre de panneaux couvrant la consommation journalière."""
    if daily_load_wh <= 0 or daily_solar_per_panel_wh <= 0:
        return 0
    return math.ceil(daily_load_wh / daily_solar_per_panel_wh)


def _find_min_batteries(
    charges,
    hourly_irradiance: list[float],
    n_panels: int,
    panel_peak_power_wp: float,
    battery_capacity_wh: float,
    dod: float,
    system_efficiency: float,
) -> int:
    """
    Simule une journée depuis batterie pleine et calcule le creux maximum.
    Ce creux détermine la capacité minimale requise.
    """
    relative_soc = 0.0
    min_relative_soc = 0.0

    for t in range(24):
        load = sum(_load_at_hour(c, t) for c in charges)
        solar = n_panels * (hourly_irradiance[t] / 1000) * panel_peak_power_wp * system_efficiency
        relative_soc += solar - load
        min_relative_soc = min(min_relative_soc, relative_soc)

    max_draw_wh = -min_relative_soc  # valeur positive : énergie max soutirée
    usable_per_battery = battery_capacity_wh * dod

    if max_draw_wh <= 0 or usable_per_battery <= 0:
        return 1
    return max(1, math.ceil(max_draw_wh / usable_per_battery))


def _simulate_30_days(
    charges,
    hourly_irradiance: list[float],
    n_panels: int,
    n_batteries: int,
    panel_peak_power_wp: float,
    battery_capacity_wh: float,
    dod: float,
    system_efficiency: float,
) -> tuple[float, float]:
    """
    Simule 30 jours et retourne les moyennes en régime établi (7 derniers jours) :
    (énergie perdue/jour, énergie manquante/jour).
    """
    max_soc = battery_capacity_wh * n_batteries
    min_soc = max_soc * (1 - dod)
    soc = max_soc * 0.5  # départ à 50 %

    daily_wasted = []
    daily_deficit = []

    for _ in range(30): # simulation des 30 jours
        day_wasted = 0.0
        day_deficit = 0.0

        for t in range(24): # simulation pour 24 heures
            load = sum(_load_at_hour(c, t) for c in charges)
            solar = n_panels * (hourly_irradiance[t] / 1000) * panel_peak_power_wp * system_efficiency
            new_soc = soc + solar - load

            if new_soc > max_soc:
                day_wasted += new_soc - max_soc
                new_soc = max_soc
            elif new_soc < min_soc:
                day_deficit += min_soc - new_soc
                new_soc = min_soc

            soc = new_soc

        daily_wasted.append(day_wasted)
        daily_deficit.append(day_deficit)

    steady_wasted = sum(daily_wasted[-7:]) / 7
    steady_deficit = sum(daily_deficit[-7:]) / 7
    return steady_wasted, steady_deficit


def compute_dimensioning(
    charges,
    hourly_irradiance: list[float],
    panel_peak_power_wp: float,
    battery_capacity_wh: float,
    battery_dod: float,
    system_efficiency: float,
) -> dict:
    hourly_loads = [sum(_load_at_hour(c, t) for c in charges) for t in range(24)]
    daily_load = sum(hourly_loads)

    daily_solar_per_panel = sum(
        (irr / 1000) * panel_peak_power_wp * system_efficiency for irr in hourly_irradiance
    )

    n_panels = _find_min_panels(daily_load, daily_solar_per_panel)
    n_batteries = _find_min_batteries(
        charges, hourly_irradiance, n_panels,
        panel_peak_power_wp, battery_capacity_wh, battery_dod, system_efficiency,
    )

    daily_solar = n_panels * daily_solar_per_panel

    avg_wasted, avg_deficit = _simulate_30_days(
        charges, hourly_irradiance, n_panels, n_batteries,
        panel_peak_power_wp, battery_capacity_wh, battery_dod, system_efficiency,
    )

    is_oversized = daily_solar > 0 and (avg_wasted / daily_solar) > 0.15

    return {
        "recommended_panels": n_panels,
        "recommended_batteries": n_batteries,
        "daily_load_wh": round(daily_load, 2),
        "daily_solar_wh": round(daily_solar, 2),
        "energy_wasted_wh_per_day": round(avg_wasted, 2),
        "energy_deficit_wh_per_day": round(avg_deficit, 2),
        "is_oversized": is_oversized,
    }
