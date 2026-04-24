import { DecimalPipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, DestroyRef, OnInit, computed, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormBuilder, FormControl, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { debounceTime, distinctUntilChanged, filter, merge, switchMap, tap } from 'rxjs';

import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

import { ProjectService } from '../../../core/services/project.service';
import { Charge } from '../../../core/models/charge.model';
import { Project } from '../../../core/models/project.model';
import { DimensioningResult } from '../../../core/models/dimensioning.model';
import { EnergyChartComponent, HourlyBreakdown } from '../energy-chart/energy-chart';

interface DerivedStats {
  daily_load_wh: number;
  daily_solar_wh: number;
  energy_wasted_wh_per_day: number;
  energy_deficit_wh_per_day: number;
  is_oversized: boolean;
}

@Component({
  selector: 'app-dimensioning',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    RouterLink,
    DecimalPipe,
    ReactiveFormsModule,
    MatButtonModule,
    MatCardModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
    MatProgressSpinnerModule,
    EnergyChartComponent,
  ],
  templateUrl: './dimensioning.html',
  styleUrl: './dimensioning.scss',
})
export class DimensioningComponent implements OnInit {
  private route = inject(ActivatedRoute);
  private projectService = inject(ProjectService);
  private fb = inject(FormBuilder);
  private destroyRef = inject(DestroyRef);

  project = signal<Project | null>(null);
  result = signal<DimensioningResult | null>(null);
  breakdown = signal<HourlyBreakdown[]>([]);
  loadingProject = signal(true);
  loadingResult = signal(false);
  irradianceNotReady = signal(false);

  projectId = this.route.snapshot.paramMap.get('id')!;

  // Paramètres physiques → appel API
  form = this.fb.group({
    panel_peak_power_wp: [400, [Validators.required, Validators.min(1)]],
    battery_capacity_wh: [200, [Validators.required, Validators.min(1)]],
    battery_dod: [0.8, [Validators.required, Validators.min(0.01), Validators.max(1)]],
    system_efficiency: [0.8, [Validators.required, Validators.min(0.01), Validators.max(1)]],
  });

  // Overrides manuels → recalcul local
  overridePanels = new FormControl<number>(0, [Validators.required, Validators.min(0)]);
  overrideBatteries = new FormControl<number>(0, [Validators.required, Validators.min(0)]);

  // Miroirs signal pour la réactivité Angular
  private overridePanelsVal = signal(0);
  private overrideBatteriesVal = signal(0);

  isOptimal = computed(() => {
    const r = this.result();
    if (!r) return true;
    return this.overridePanelsVal() === r.recommended_panels &&
           this.overrideBatteriesVal() === r.recommended_batteries;
  });

  stats = computed<DerivedStats>(() => {
    const b = this.breakdown();
    if (b.length === 0) {
      return { daily_load_wh: 0, daily_solar_wh: 0, energy_wasted_wh_per_day: 0, energy_deficit_wh_per_day: 0, is_oversized: false };
    }
    const daily_load_wh = b.reduce((s, h) => s + h.load_wh, 0);
    const daily_solar_wh = b.reduce((s, h) => s + h.solar_wh + h.solar_wasted_wh, 0);
    const energy_wasted_wh_per_day = b.reduce((s, h) => s + h.solar_wasted_wh, 0);
    const energy_deficit_wh_per_day = b.reduce((s, h) => s + h.deficit_wh, 0);
    const is_oversized = daily_solar_wh > 0 && (energy_wasted_wh_per_day / daily_solar_wh) > 0.15;
    return { daily_load_wh, daily_solar_wh, energy_wasted_wh_per_day, energy_deficit_wh_per_day, is_oversized };
  });

  ngOnInit() {
    this.projectService.get(this.projectId).subscribe({
      next: p => {
        this.project.set(p);
        this.loadingProject.set(false);
        this.subscribeToParamChanges();
        this.subscribeToOverrideChanges();
        this.form.updateValueAndValidity({ emitEvent: true });
      },
    });
  }

  resetToOptimal() {
    const r = this.result();
    if (!r) return;
    this.overridePanels.setValue(r.recommended_panels);
    this.overrideBatteries.setValue(r.recommended_batteries);
  }

  stepPanels(delta: number): void {
    const next = Math.max(0, (this.overridePanels.value ?? 0) + delta);
    this.overridePanels.setValue(next);
  }

  stepBatteries(delta: number): void {
    const next = Math.max(0, (this.overrideBatteries.value ?? 0) + delta);
    this.overrideBatteries.setValue(next);
  }

  private subscribeToParamChanges() {
    this.form.valueChanges.pipe(
      debounceTime(600),
      distinctUntilChanged((a, b) => JSON.stringify(a) === JSON.stringify(b)),
      filter(() => this.form.valid),
      switchMap(() => {
        const v = this.form.value;
        this.loadingResult.set(true);
        this.irradianceNotReady.set(false);
        return this.projectService.getDimensioning(this.projectId, {
          panel_peak_power_wp: v.panel_peak_power_wp!,
          battery_capacity_wh: v.battery_capacity_wh!,
          battery_dod: v.battery_dod!,
          system_efficiency: v.system_efficiency!,
        });
      }),
      takeUntilDestroyed(this.destroyRef),
    ).subscribe({
      next: result => {
        this.result.set(result);
        this.loadingResult.set(false);
        this.overridePanels.setValue(result.recommended_panels, { emitEvent: false });
        this.overrideBatteries.setValue(result.recommended_batteries, { emitEvent: false });
        this.overridePanelsVal.set(result.recommended_panels);
        this.overrideBatteriesVal.set(result.recommended_batteries);
        this.recomputeBreakdown();
      },
      error: (err: HttpErrorResponse) => {
        this.loadingResult.set(false);
        if (err.status === 409) this.irradianceNotReady.set(true);
      },
    });
  }

  private subscribeToOverrideChanges() {
    merge(
      this.overridePanels.valueChanges.pipe(tap(v => this.overridePanelsVal.set(v ?? 0))),
      this.overrideBatteries.valueChanges.pipe(tap(v => this.overrideBatteriesVal.set(v ?? 0))),
    ).pipe(
      debounceTime(300),
      takeUntilDestroyed(this.destroyRef),
    ).subscribe(() => this.recomputeBreakdown());
  }

  private recomputeBreakdown() {
    const p = this.project();
    const nPanels = this.overridePanels.value ?? 0;
    const nBatteries = this.overrideBatteries.value ?? 0;
    if (p?.hourly_irradiance) {
      this.breakdown.set(this.computeBreakdown(p, nPanels, nBatteries));
    }
  }

  private computeBreakdown(project: Project, nPanels: number, nBatteries: number): HourlyBreakdown[] {
    const v = this.form.value;
    const panelWp = v.panel_peak_power_wp!;
    const batWh = v.battery_capacity_wh!;
    const dod = v.battery_dod!;
    const efficiency = v.system_efficiency!;

    const maxSoc = batWh * nBatteries;
    const minSoc = maxSoc * (1 - dod);

    // 3 cycles de chauffe pour converger vers l'état stable
    let soc = maxSoc / 2;
    for (let cycle = 0; cycle < 3; cycle++) {
      for (let h = 0; h < 24; h++) {
        const load = this.loadAtHour(project.charges, h);
        const solar = (project.hourly_irradiance![h] / 1000) * panelWp * nPanels * efficiency;
        const net = solar - load;
        if (net >= 0) {
          soc = Math.min(maxSoc, soc + net);
        } else {
          soc -= Math.min(-net, Math.max(0, soc - minSoc));
        }
      }
    }

    // 4ᵉ cycle : calcul réel avec état stable
    return Array.from({ length: 24 }, (_, h) => {
      const load_wh = this.loadAtHour(project.charges, h);
      const solar_produced = (project.hourly_irradiance![h] / 1000) * panelWp * nPanels * efficiency;
      const net = solar_produced - load_wh;

      let solar_wh: number, solar_wasted_wh: number, battery_wh: number, deficit_wh: number;

      if (net >= 0) {
        solar_wh = load_wh;
        const charged = Math.min(net, maxSoc - soc);
        solar_wasted_wh = net - charged;
        battery_wh = 0;
        deficit_wh = 0;
        soc = Math.min(maxSoc, soc + net);
      } else {
        solar_wh = solar_produced;
        solar_wasted_wh = 0;
        const needed = -net;
        const available = Math.max(0, soc - minSoc);
        battery_wh = Math.min(needed, available);
        deficit_wh = needed - battery_wh;
        soc -= battery_wh;
      }

      return { hour: h, load_wh, solar_wh, solar_wasted_wh, battery_wh, deficit_wh };
    });
  }

  private loadAtHour(charges: Charge[], hour: number): number {
    return charges.reduce((sum, charge) => {
      const slot = charge.hourly_slots.find(s => s.hour === hour);
      if (!slot || slot.state === 'INACTIVE') return sum;
      if (slot.state === 'ACTIVE') return sum + charge.max_power_w * charge.real_usage_rate;
      return sum + (slot.custom_value_w ?? 0);
    }, 0);
  }
}
