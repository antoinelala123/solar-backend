import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', redirectTo: 'projects', pathMatch: 'full' },
  {
    path: 'projects',
    loadComponent: () =>
      import('./features/projects/project-list/project-list').then(m => m.ProjectListComponent),
  },
  {
    path: 'projects/:id',
    loadComponent: () =>
      import('./features/projects/project-detail/project-detail').then(m => m.ProjectDetailComponent),
  },
  {
    path: 'projects/:id/dimensioning',
    loadComponent: () =>
      import('./features/dimensioning/dimensioning/dimensioning').then(m => m.DimensioningComponent),
  },
];
