import { DecimalPipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';

export interface HourlyBreakdown {
  hour: number;
  load_wh: number;
  solar_wh: number;
  solar_wasted_wh: number;
  battery_wh: number;
  deficit_wh: number;
}

@Component({
  selector: 'app-energy-chart',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [DecimalPipe],
  templateUrl: './energy-chart.html',
  styleUrl: './energy-chart.scss',
})
export class EnergyChartComponent {
  breakdown = input.required<HourlyBreakdown[]>();

  maxLoad = computed(() => Math.max(...this.breakdown().map(b => b.load_wh), 1));

  yTicks = computed(() => {
    const max = this.maxLoad();
    const step = this.niceStep(max);
    const ticks: number[] = [];
    for (let v = step; v <= max * 1.01; v += step) {
      ticks.push(Math.round(v));
    }
    return ticks;
  });

  tickPercent(tick: number): number {
    return (tick / this.maxLoad()) * 100;
  }

  barHeight(b: HourlyBreakdown): number {
    if (b.load_wh <= 0) return 0;
    return Math.max((b.load_wh / this.maxLoad()) * 100, 2);
  }

  solarPct(b: HourlyBreakdown): number {
    return b.load_wh > 0 ? (b.solar_wh / b.load_wh) * 100 : 0;
  }

  batteryPct(b: HourlyBreakdown): number {
    return b.load_wh > 0 ? (b.battery_wh / b.load_wh) * 100 : 0;
  }

  deficitPct(b: HourlyBreakdown): number {
    return b.load_wh > 0 ? (b.deficit_wh / b.load_wh) * 100 : 0;
  }

  private niceStep(max: number): number {
    if (max <= 200) return 50;
    if (max <= 500) return 100;
    if (max <= 2000) return 500;
    if (max <= 5000) return 1000;
    if (max <= 10000) return 2000;
    return 5000;
  }
}
