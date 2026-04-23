import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';

@Component({
  selector: 'app-create-project-dialog',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [ReactiveFormsModule, MatDialogModule, MatFormFieldModule, MatInputModule, MatButtonModule],
  template: `
    <h2 mat-dialog-title>Nouveau projet</h2>

    <mat-dialog-content>
      <form [formGroup]="form" id="create-form" (ngSubmit)="submit()">
        <mat-form-field appearance="outline">
          <mat-label>Nom du projet</mat-label>
          <input matInput formControlName="name" />
          @if (form.controls.name.hasError('required')) {
            <mat-error>Champ requis</mat-error>
          }
        </mat-form-field>

        <mat-form-field appearance="outline">
          <mat-label>Latitude (-90 à 90)</mat-label>
          <input matInput type="number" formControlName="gps_lat" />
          @if (form.controls.gps_lat.hasError('required')) {
            <mat-error>Champ requis</mat-error>
          }
          @if (form.controls.gps_lat.hasError('min') || form.controls.gps_lat.hasError('max')) {
            <mat-error>Entre -90 et 90</mat-error>
          }
        </mat-form-field>

        <mat-form-field appearance="outline">
          <mat-label>Longitude (-180 à 180)</mat-label>
          <input matInput type="number" formControlName="gps_lon" />
          @if (form.controls.gps_lon.hasError('required')) {
            <mat-error>Champ requis</mat-error>
          }
          @if (form.controls.gps_lon.hasError('min') || form.controls.gps_lon.hasError('max')) {
            <mat-error>Entre -180 et 180</mat-error>
          }
        </mat-form-field>
      </form>
    </mat-dialog-content>

    <mat-dialog-actions align="end">
      <button mat-button mat-dialog-close>Annuler</button>
      <button mat-raised-button color="primary" form="create-form" type="submit" [disabled]="form.invalid">
        Créer
      </button>
    </mat-dialog-actions>
  `,
  styles: `
    mat-dialog-content {
      display: flex;
      flex-direction: column;
      gap: 8px;
      padding-top: 8px !important;
      min-width: 360px;
    }
    mat-form-field { width: 100%; }
  `,
})
export class CreateProjectDialogComponent {
  private fb = inject(FormBuilder);
  private dialogRef = inject(MatDialogRef<CreateProjectDialogComponent>);

  form = this.fb.group({
    name: ['', Validators.required],
    gps_lat: [null as number | null, [Validators.required, Validators.min(-90), Validators.max(90)]],
    gps_lon: [null as number | null, [Validators.required, Validators.min(-180), Validators.max(180)]],
  });

  submit() {
    if (this.form.valid) {
      this.dialogRef.close(this.form.value);
    }
  }
}
