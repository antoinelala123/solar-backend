import { DecimalPipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, computed, inject, input, output } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { HourlySlot, SlotState } from '../../../core/models/charge.model';
import { CustomValueDialogComponent } from '../custom-value-dialog/custom-value-dialog';

@Component({
  selector: 'app-hourly-chart',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [DecimalPipe],
  templateUrl: './hourly-chart.html',
  styleUrl: './hourly-chart.scss',
})
export class HourlyChartComponent {
  private dialog = inject(MatDialog);

  slots = input.required<HourlySlot[]>();
  maxPowerW = input.required<number>();
  realUsageRate = input(1);
  readOnly = input(false);

  slotChange = output<HourlySlot[]>();

  maxValue = computed(() => {
    const activeValue = this.maxPowerW() * this.realUsageRate();
    const customMax = Math.max(...this.slots().map(s => s.custom_value_w ?? 0), 0);
    return Math.max(activeValue, customMax, 1);
  });

  yTicks = computed(() => {
    const max = this.maxValue();
    const step = this.niceStep(max);
    const ticks: number[] = [];
    for (let v = step; v <= max * 1.01; v += step) {
      ticks.push(Math.round(v));
    }
    return ticks;
  });

  tickPercent(tick: number): number {
    return (tick / this.maxValue()) * 100;
  }

  private niceStep(max: number): number {
    if (max <= 200) return 50;
    if (max <= 500) return 100;
    if (max <= 2000) return 500;
    if (max <= 5000) return 1000;
    if (max <= 10000) return 2000;
    return 5000;
  }

  valueAt(slot: HourlySlot): number {
    if (slot.state === 'INACTIVE') return 0;
    if (slot.state === 'ACTIVE') return this.maxPowerW() * this.realUsageRate();
    return slot.custom_value_w ?? 0;
  }

  barHeightPercent(slot: HourlySlot): number {
    const val = this.valueAt(slot);
    if (val <= 0) return 0;
    return Math.max((val / this.maxValue()) * 100, 3);
  }

  onHourClick(slot: HourlySlot) {
    if (this.readOnly()) return;
    const next: SlotState = slot.state === 'INACTIVE' ? 'ACTIVE' : 'INACTIVE';
    this.emit({ ...slot, state: next, custom_value_w: null });
  }

  onBarClick(slot: HourlySlot) {
    if (this.readOnly() || slot.state === 'INACTIVE') return;
    const current =
      slot.state === 'CUSTOM'
        ? (slot.custom_value_w ?? 0)
        : this.maxPowerW() * this.realUsageRate();

    this.dialog
      .open(CustomValueDialogComponent, {
        data: { current, maxPowerW: this.maxPowerW() },
        width: '300px',
      })
      .afterClosed()
      .subscribe((value?: number) => {
        if (value === undefined || value === null) return;
        this.emit({ ...slot, state: 'CUSTOM', custom_value_w: value });
      });
  }

  private emit(updated: HourlySlot) {
    this.slotChange.emit(this.slots().map(s => (s.hour === updated.hour ? updated : s)));
  }
}
