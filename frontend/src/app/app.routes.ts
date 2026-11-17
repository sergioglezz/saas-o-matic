import { Routes } from '@angular/router';
import { CustomerDetailPage } from './features/customers/customer-detail-page';
import { CustomerFormPage } from './features/customers/customer-form-page';
import { CustomerListPage } from './features/customers/customer-list-page';
import { NotFoundPage } from './shared/ui/not-found-page';

/** Spec 005 §5.1 (D-15): addresses in Spanish, and «Página no encontrada» for any other. */
export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'clientes' },
  { path: 'clientes', component: CustomerListPage },
  { path: 'clientes/nuevo', component: CustomerFormPage },
  { path: 'clientes/:id', component: CustomerDetailPage },
  { path: '**', component: NotFoundPage },
];
