import { DecimalPipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, computed, inject, signal } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatDialog } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatTooltipModule } from '@angular/material/tooltip';

import { ProjectService } from '../../../core/services/project.service';
import { ChargeService } from '../../../core/services/charge.service';
import { Project } from '../../../core/models/project.model';
import { Charge, ChargeCreate, HourlySlot, SlotState } from '../../../core/models/charge.model';
import { HourlyChartComponent } from '../hourly-chart/hourly-chart';
import { CreateChargeDialogComponent } from '../create-charge-dialog/create-charge-dialog';

@Component({
  selector: 'app-project-detail',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    RouterLink,
    DecimalPipe,
    MatButtonModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatTooltipModule,
    HourlyChartComponent,
  ],
  templateUrl: './project-detail.html',
  styleUrl: './project-detail.scss',
})
export class ProjectDetailComponent implements OnInit {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private projectService = inject(ProjectService);
  private chargeService = inject(ChargeService);
  private dialog = inject(MatDialog);
  private snackBar = inject(MatSnackBar);

  project = signal<Project | null>(null);
  loading = signal(true);
  saving = signal(false);
  selectedId = signal<string | 'total'>('total');

  selectedCharge = computed(() => {
    const id = this.selectedId();
    if (id === 'total') return null;
    return this.project()?.charges.find(c => c.id === id) ?? null;
  });

  totalSlots = computed<HourlySlot[]>(() => {
    const charges = this.project()?.charges ?? [];
    return Array.from({ length: 24 }, (_, h) => ({
      hour: h,
      state: 'CUSTOM' as SlotState,
      custom_value_w: charges.reduce((sum, charge) => {
        const slot = charge.hourly_slots.find(s => s.hour === h);
        if (!slot || slot.state === 'INACTIVE') return sum;
        if (slot.state === 'ACTIVE') return sum + charge.max_power_w * charge.real_usage_rate;
        return sum + (slot.custom_value_w ?? 0);
      }, 0),
    }));
  });

  totalMaxW = computed(() =>
    (this.project()?.charges ?? []).reduce((sum, c) => sum + c.max_power_w, 0)
  );

  ngOnInit() {
    const id = this.route.snapshot.paramMap.get('id')!;
    this.projectService.get(id).subscribe({
      next: p => {
        this.project.set(p);
        this.loading.set(false);
      },
      error: () => {
        this.snackBar.open('Projet introuvable', 'OK', { duration: 3000 });
        this.router.navigate(['/projects']);
      },
    });
  }

  openCreateCharge() {
    this.dialog
      .open(CreateChargeDialogComponent, { width: '420px' })
      .afterClosed()
      .subscribe((data?: Omit<ChargeCreate, 'hourly_slots'>) => {
        if (!data) return;
        const slots: HourlySlot[] = Array.from({ length: 24 }, (_, h) => ({
          hour: h,
          state: 'INACTIVE',
          custom_value_w: null,
        }));
        this.chargeService.create(this.project()!.id, { ...data, hourly_slots: slots }).subscribe({
          next: charge => {
            this.project.update(p => (p ? { ...p, charges: [...p.charges, charge] } : p));
            this.selectedId.set(charge.id);
          },
          error: () => this.snackBar.open('Erreur lors de la création', 'OK', { duration: 3000 }),
        });
      });
  }

  deleteCharge(charge: Charge) {
    this.chargeService.delete(charge.id).subscribe({
      next: () => {
        if (this.selectedId() === charge.id) this.selectedId.set('total');
        this.project.update(p =>
          p ? { ...p, charges: p.charges.filter(c => c.id !== charge.id) } : p
        );
      },
      error: () => this.snackBar.open('Erreur lors de la suppression', 'OK', { duration: 3000 }),
    });
  }

  onSlotChange(updatedSlots: HourlySlot[]) {
    const charge = this.selectedCharge();
    if (!charge) return;
    const payload: ChargeCreate = {
      name: charge.name,
      max_power_w: charge.max_power_w,
      real_usage_rate: charge.real_usage_rate,
      hourly_slots: updatedSlots,
    };
    this.saving.set(true);
    this.chargeService.update(charge.id, payload).subscribe({
      next: saved => {
        this.project.update(p =>
          p ? { ...p, charges: p.charges.map(c => (c.id === saved.id ? saved : c)) } : p
        );
        this.saving.set(false);
      },
      error: () => {
        this.snackBar.open('Erreur lors de la sauvegarde', 'OK', { duration: 3000 });
        this.saving.set(false);
      },
    });
  }
}
