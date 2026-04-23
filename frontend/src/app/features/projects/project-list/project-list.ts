import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatDialog } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar } from '@angular/material/snack-bar';

import { ProjectService } from '../../../core/services/project.service';
import { Project } from '../../../core/models/project.model';
import { CreateProjectDialogComponent } from '../create-project-dialog/create-project-dialog';

@Component({
  selector: 'app-project-list',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [MatCardModule, MatButtonModule, MatIconModule, MatProgressSpinnerModule],
  templateUrl: './project-list.html',
  styleUrl: './project-list.scss',
})
export class ProjectListComponent implements OnInit {
  private projectService = inject(ProjectService);
  private router = inject(Router);
  private dialog = inject(MatDialog);
  private snackBar = inject(MatSnackBar);

  projects = signal<Project[]>([]);
  loading = signal(true);

  ngOnInit() {
    this.load();
  }

  load() {
    this.loading.set(true);
    this.projectService.list().subscribe({
      next: (list) => {
        this.projects.set(list);
        this.loading.set(false);
      },
      error: () => {
        this.snackBar.open('Erreur lors du chargement', 'OK', { duration: 3000 });
        this.loading.set(false);
      },
    });
  }

  openCreate() {
    this.dialog
      .open(CreateProjectDialogComponent, { width: '420px' })
      .afterClosed()
      .subscribe((data) => {
        if (!data) return;
        this.projectService.create(data).subscribe({
          next: (project) => {
            this.projects.update((list) => [...list, project]);
            this.snackBar.open(`Projet "${project.name}" créé`, 'OK', { duration: 3000 });
          },
          error: () => this.snackBar.open('Erreur lors de la création', 'OK', { duration: 3000 }),
        });
      });
  }

  delete(event: Event, project: Project) {
    event.stopPropagation();
    this.projectService.delete(project.id).subscribe({
      next: () => {
        this.projects.update((list) => list.filter((p) => p.id !== project.id));
        this.snackBar.open(`Projet "${project.name}" supprimé`, 'OK', { duration: 3000 });
      },
      error: () => this.snackBar.open('Erreur lors de la suppression', 'OK', { duration: 3000 }),
    });
  }

  navigate(id: string) {
    this.router.navigate(['/projects', id]);
  }
}
