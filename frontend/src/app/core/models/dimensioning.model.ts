export interface DimensioningResult {
  recommended_panels: number;
  recommended_batteries: number;
  daily_load_wh: number;
  daily_solar_wh: number;
  energy_wasted_wh_per_day: number;
  energy_deficit_wh_per_day: number;
  is_oversized: boolean;
}

export interface DimensioningParams {
  panel_peak_power_wp: number;
  battery_capacity_wh: number;
  battery_dod: number;
  system_efficiency: number;
}
