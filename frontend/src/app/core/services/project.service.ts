import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Project, ProjectCreate } from '../models/project.model';
import { DimensioningResult, DimensioningParams } from '../models/dimensioning.model';

@Injectable({ providedIn: 'root' })
export class ProjectService {
  private http = inject(HttpClient);
  private base = '/api/projects';

  list(): Observable<Project[]> {
    return this.http.get<Project[]>(this.base);
  }

  get(id: string): Observable<Project> {
    return this.http.get<Project>(`${this.base}/${id}`);
  }

  create(data: ProjectCreate): Observable<Project> {
    return this.http.post<Project>(this.base, data);
  }

  delete(id: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/${id}`);
  }

  getDimensioning(id: string, params: DimensioningParams): Observable<DimensioningResult> {
    const httpParams = new HttpParams()
      .set('panel_peak_power_wp', params.panel_peak_power_wp)
      .set('battery_capacity_wh', params.battery_capacity_wh)
      .set('battery_dod', params.battery_dod)
      .set('system_efficiency', params.system_efficiency);
    return this.http.get<DimensioningResult>(`${this.base}/${id}/dimensioning`, { params: httpParams });
  }
}
