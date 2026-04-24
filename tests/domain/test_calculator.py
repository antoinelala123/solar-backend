import pytest
from backend.domain.entities import HourlySlot
from backend.domain.calculator import (
    _load_at_hour,
    _find_min_panels,
    _find_min_batteries,
    _simulate_30_days,
    compute_dimensioning,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def make_charge(max_power_w: float, real_usage_rate: float, slots: list[dict]):
    """Objet minimal simulant un Charge ORM."""
    class _Charge:
        pass
    c = _Charge()
    c.max_power_w = max_power_w
    c.real_usage_rate = real_usage_rate
    c.hourly_slots = slots
    return c


def make_slots(active_hours: list[int] = [], custom: dict[int, float] = {}) -> list[HourlySlot]:
    """Génère 24 slots : ACTIVE sur active_hours, CUSTOM sur custom, INACTIVE ailleurs."""
    slots = []
    for h in range(24):
        if h in custom:
            slots.append(HourlySlot(hour=h, state="CUSTOM", custom_value_w=custom[h]))
        elif h in active_hours:
            slots.append(HourlySlot(hour=h, state="ACTIVE", custom_value_w=None))
        else:
            slots.append(HourlySlot(hour=h, state="INACTIVE", custom_value_w=None))
    return slots


def flat_irradiance(value: float) -> list[float]:
    """Irradiance constante sur 24h (cas simplifié pour les calculs)."""
    return [value] * 24


def solar_irradiance_profile() -> list[float]:
    """Profil réaliste : soleil de 6h à 18h, pic à midi."""
    profile = [0.0] * 24
    for h in range(6, 19):
        profile[h] = 500.0 * (1 - abs(h - 12) / 6)
    return profile


# ── Tests _load_at_hour ────────────────────────────────────────────────────────

def test_load_inactive_retourne_zero():
    charge = make_charge(1000.0, 0.8, make_slots(active_hours=[]))
    assert _load_at_hour(charge, 10) == 0.0


def test_load_active_applique_real_usage_rate():
    charge = make_charge(1000.0, 0.8, make_slots(active_hours=[10]))
    assert _load_at_hour(charge, 10) == 800.0  # 1000 × 0.8


def test_load_custom_retourne_custom_value():
    charge = make_charge(1000.0, 0.8, make_slots(custom={10: 300.0}))
    assert _load_at_hour(charge, 10) == 300.0  # real_usage_rate ignoré


def test_load_heure_absente_retourne_zero():
    charge = make_charge(1000.0, 0.8, [])  # aucun slot
    assert _load_at_hour(charge, 5) == 0.0


# ── Tests _find_min_panels ─────────────────────────────────────────────────────

def test_find_min_panels_calcul_de_base():
    # 1000 Wh/jour à couvrir, chaque panneau produit 500 Wh/jour → 2 panneaux
    assert _find_min_panels(1000.0, 500.0) == 2


def test_find_min_panels_arrondi_superieur():
    # 1100 Wh / 500 Wh = 2.2 → 3 panneaux
    assert _find_min_panels(1100.0, 500.0) == 3


def test_find_min_panels_pas_de_charge():
    assert _find_min_panels(0.0, 500.0) == 0


def test_find_min_panels_pas_de_soleil():
    assert _find_min_panels(1000.0, 0.0) == 0


# ── Tests _find_min_batteries ──────────────────────────────────────────────────

def test_find_min_batteries_retourne_au_moins_1():
    # Panneau couvre toute la consommation → pas de creux → 1 batterie minimum
    charge = make_charge(100.0, 1.0, make_slots(active_hours=[12]))  # 100 Wh à midi
    irr = flat_irradiance(1000.0)  # soleil toute la journée
    # 1 panneau de 400 Wp produit 400 Wh à midi → largement suffisant
    result = _find_min_batteries([charge], irr, 1, 400.0, 200.0, 0.8, 0.8)
    assert result >= 1


def test_find_min_batteries_couvre_deficit_nuit():
    # Charge active la nuit uniquement (20h-22h) : 500 Wh
    # Panneaux ne produisent rien la nuit → batterie doit tout couvrir
    charge = make_charge(500.0, 1.0, make_slots(active_hours=[20, 21]))
    irr = [0.0] * 24  # aucun soleil (cas extrême)
    # usable = 200 Wh × 0.8 = 160 Wh → besoin 1000 Wh → 7 batteries
    result = _find_min_batteries([charge], irr, 0, 400.0, 200.0, 0.8, 0.8)
    assert result == 7  # ceil(1000 / 160)


# ── Tests _simulate_30_days ────────────────────────────────────────────────────

def test_simulate_systeme_equilibre_pas_de_perte():
    """Production = consommation exacte → pas de perte ni déficit en régime établi."""
    # Charge de 100 Wh toutes les heures = 2400 Wh/jour
    # 1 panneau de 100 Wp sous 1000 W/m² constante = 100 Wh × 24h = 2400 Wh/jour
    charge = make_charge(100.0, 1.0, make_slots(active_hours=list(range(24))))
    irr = flat_irradiance(1000.0)

    wasted, deficit = _simulate_30_days([charge], irr, 1, 1, 100.0, 5000.0, 1.0, 1.0)

    assert wasted == pytest.approx(0.0, abs=1.0)
    assert deficit == pytest.approx(0.0, abs=1.0)


def test_simulate_surdimensionne_produit_des_pertes():
    """Beaucoup de panneaux pour peu de charge → batterie pleine → pertes."""
    charge = make_charge(50.0, 1.0, make_slots(active_hours=[12]))  # 50 Wh/jour
    irr = solar_irradiance_profile()

    wasted, deficit = _simulate_30_days([charge], irr, 10, 1, 400.0, 200.0, 0.8, 0.8)

    assert wasted > 0


def test_simulate_sous_dimensionne_produit_des_deficits():
    """Pas assez de panneaux ni batteries → déficits."""
    charge = make_charge(2000.0, 1.0, make_slots(active_hours=list(range(24))))
    irr = [0.0] * 24  # pas de soleil

    wasted, deficit = _simulate_30_days([charge], irr, 0, 1, 200.0, 0.8, 1.0, 1.0)

    assert deficit > 0


# ── Tests compute_dimensioning ─────────────────────────────────────────────────

def test_compute_dimensioning_retourne_structure_complete():
    charge = make_charge(200.0, 0.8, make_slots(active_hours=[8, 9, 18, 19]))
    irr = solar_irradiance_profile()

    result = compute_dimensioning([charge], irr, 400.0, 200.0, 0.8, 0.8)

    assert "recommended_panels" in result
    assert "recommended_batteries" in result
    assert "daily_load_wh" in result
    assert "daily_solar_wh" in result
    assert "energy_wasted_wh_per_day" in result
    assert "energy_deficit_wh_per_day" in result
    assert "is_oversized" in result


def test_compute_dimensioning_sans_charge():
    result = compute_dimensioning([], solar_irradiance_profile(), 400.0, 200.0, 0.8, 0.8)
    assert result["recommended_panels"] == 0
    assert result["daily_load_wh"] == 0.0


def test_compute_dimensioning_is_oversized_si_beaucoup_de_perte():
    """Un panneau de 10 kWc pour 50 Wh/jour de besoin doit être flaggé oversized."""
    charge = make_charge(50.0, 1.0, make_slots(active_hours=[12]))
    irr = solar_irradiance_profile()

    result = compute_dimensioning([charge], irr, 10_000.0, 200.0, 0.8, 0.8)

    assert result["is_oversized"] is True
    assert result["energy_wasted_wh_per_day"] > 0


def test_compute_dimensioning_not_oversized_si_bien_dimensionne():
    """Charge répartie sur 24h avec grande batterie → production = consommation → pas oversized."""
    # 100 W toutes les heures = 2400 Wh/jour
    # 2 panneaux de 400 Wp produisent aussi ~2400 Wh/jour
    # Grande batterie (2000 Wh) pour absorber le décalage jour/nuit sans déborder
    charge = make_charge(100.0, 1.0, make_slots(active_hours=list(range(24))))
    irr = solar_irradiance_profile()

    result = compute_dimensioning([charge], irr, 400.0, 2000.0, 0.8, 1.0)

    assert result["is_oversized"] is False


def test_compute_daily_load_est_correct():
    # 2 heures actives × 500 W × 0.8 = 800 Wh
    charge = make_charge(500.0, 0.8, make_slots(active_hours=[10, 14]))
    irr = solar_irradiance_profile()

    result = compute_dimensioning([charge], irr, 400.0, 200.0, 0.8, 0.8)

    assert result["daily_load_wh"] == pytest.approx(800.0)
