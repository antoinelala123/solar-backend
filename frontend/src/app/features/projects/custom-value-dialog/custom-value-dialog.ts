import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { FormControl, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';

interface DialogData {
  current: number;
  maxPowerW: number;
}

@Component({
  selector: 'app-custom-value-dialog',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [ReactiveFormsModule, MatDialogModule, MatFormFieldModule, MatInputModule, MatButtonModule],
  template: `
    <h2 mat-dialog-title>Valeur personnalisée</h2>

    <mat-dialog-content>
      <mat-form-field appearance="outline">
        <mat-label>Puissance (W)</mat-label>
        <input matInput type="number" [formControl]="valueControl" min="0" [max]="data.maxPowerW" />
        <mat-hint>Entre 0 et {{ data.maxPowerW }} W</mat-hint>
        @if (valueControl.hasError('min') || valueControl.hasError('max')) {
          <mat-error>Entre 0 et {{ data.maxPowerW }} W</mat-error>
        }
      </mat-form-field>
    </mat-dialog-content>

    <mat-dialog-actions align="end">
      <button mat-button mat-dialog-close>Annuler</button>
      <button mat-raised-button color="primary" [disabled]="valueControl.invalid" (click)="confirm()">
        Confirmer
      </button>
    </mat-dialog-actions>
  `,
  styles: `
    mat-dialog-content { padding-top: 8px !important; min-width: 280px; }
    mat-form-field { width: 100%; }
  `,
})
export class CustomValueDialogComponent {
  data = inject<DialogData>(MAT_DIALOG_DATA);
  private dialogRef = inject(MatDialogRef<CustomValueDialogComponent>);

  valueControl = new FormControl(this.data.current, [
    Validators.required,
    Validators.min(0),
    Validators.max(this.data.maxPowerW),
  ]);

  confirm() {
    if (this.valueControl.valid) {
      this.dialogRef.close(this.valueControl.value as number);
    }
  }
}
