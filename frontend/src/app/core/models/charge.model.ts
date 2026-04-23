export type SlotState = 'INACTIVE' | 'ACTIVE' | 'CUSTOM';

export interface HourlySlot {
  hour: number;
  state: SlotState;
  custom_value_w: number | null;
}

export interface Charge {
  id: string;
  project_id: string;
  name: string;
  max_power_w: number;
  real_usage_rate: number;
  hourly_slots: HourlySlot[];
}

export interface ChargeCreate {
  name: string;
  max_power_w: number;
  real_usage_rate: number;
  hourly_slots: HourlySlot[];
}
