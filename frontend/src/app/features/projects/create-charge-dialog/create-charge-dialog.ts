import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';

@Component({
  selector: 'app-create-charge-dialog',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [ReactiveFormsModule, MatDialogModule, MatFormFieldModule, MatInputModule, MatButtonModule],
  template: `
    <h2 mat-dialog-title>Nouvelle charge</h2>

    <mat-dialog-content>
      <form [formGroup]="form" id="charge-form" (ngSubmit)="submit()">
        <mat-form-field appearance="outline">
          <mat-label>Nom de l'appareil</mat-label>
          <input matInput formControlName="name" />
          @if (form.controls.name.hasError('required')) {
            <mat-error>Champ requis</mat-error>
          }
        </mat-form-field>

        <mat-form-field appearance="outline">
          <mat-label>Puissance nominale (W)</mat-label>
          <input matInput type="number" formControlName="max_power_w" min="0" />
          @if (form.controls.max_power_w.hasError('required')) {
            <mat-error>Champ requis</mat-error>
          }
          @if (form.controls.max_power_w.hasError('min')) {
            <mat-error>Valeur positive requise</mat-error>
          }
        </mat-form-field>

        <mat-form-field appearance="outline">
          <mat-label>Taux d'usage réel (0 à 1)</mat-label>
          <input matInput type="number" formControlName="real_usage_rate" min="0" max="1" step="0.05" />
          <mat-hint>Ex: 0.8 = 80 % de la puissance nominale</mat-hint>
          @if (form.controls.real_usage_rate.hasError('min') || form.controls.real_usage_rate.hasError('max')) {
            <mat-error>Entre 0 et 1</mat-error>
          }
        </mat-form-field>
      </form>
    </mat-dialog-content>

    <mat-dialog-actions align="end">
      <button mat-button mat-dialog-close>Annuler</button>
      <button mat-raised-button color="primary" form="charge-form" type="submit" [disabled]="form.invalid">
        Créer
      </button>
    </mat-dialog-actions>
  `,
  styles: `
    mat-dialog-content { display: flex; flex-direction: column; gap: 8px; padding-top: 8px !important; min-width: 360px; }
    mat-form-field { width: 100%; }
  `,
})
export class CreateChargeDialogComponent {
  private fb = inject(FormBuilder);
  private dialogRef = inject(MatDialogRef<CreateChargeDialogComponent>);

  form = this.fb.group({
    name: ['', Validators.required],
    max_power_w: [null as number | null, [Validators.required, Validators.min(0.001)]],
    real_usage_rate: [1.0, [Validators.required, Validators.min(0), Validators.max(1)]],
  });

  submit() {
    if (this.form.valid) {
      this.dialogRef.close(this.form.value);
    }
  }
}
