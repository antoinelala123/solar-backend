import { Charge } from './charge.model';

export interface Project {
  id: string;
  name: string;
  gps_lat: number;
  gps_lon: number;
  hourly_irradiance: number[] | null;
  created_at: string;
  charges: Charge[];
}

export interface ProjectCreate {
  name: string;
  gps_lat: number;
  gps_lon: number;
}
