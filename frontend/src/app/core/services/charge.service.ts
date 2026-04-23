import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Charge, ChargeCreate } from '../models/charge.model';

@Injectable({ providedIn: 'root' })
export class ChargeService {
  private http = inject(HttpClient);

  create(projectId: string, data: ChargeCreate): Observable<Charge> {
    return this.http.post<Charge>(`/api/projects/${projectId}/charges`, data);
  }

  update(chargeId: string, data: ChargeCreate): Observable<Charge> {
    return this.http.put<Charge>(`/api/charges/${chargeId}`, data);
  }

  delete(chargeId: string): Observable<void> {
    return this.http.delete<void>(`/api/charges/${chargeId}`);
  }
}
