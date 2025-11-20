import { useState } from 'react';
import type { FormEvent } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { createItem, fetchList } from '../api';
import { DataTable } from '../components/DataTable';
import type { Employee } from '../types';

const blankEmployee = {
  user: '',
  full_name: '',
  department: '',
  position: '',
  role: '',
};

const StaffPage = () => {
  const queryClient = useQueryClient();
  const [form, setForm] = useState(blankEmployee);

  const { data: employees = [] } = useQuery({
    queryKey: ['employees'],
    queryFn: () => fetchList<Employee>('employees/'),
  });

  const createEmployee = useMutation({
    mutationFn: (payload: Record<string, unknown>) => createItem('employees/', payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['employees'] });
      setForm(blankEmployee);
    },
  });

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!form.user || !form.full_name) return;
    createEmployee.mutate({
      user_id: Number(form.user),
      full_name: form.full_name,
      department: form.department ? Number(form.department) : null,
      position: form.position ? Number(form.position) : null,
      role: form.role ? Number(form.role) : null,
    });
  };

  return (
    <div className="page">
      <h1>Сотрудники</h1>

      <section>
        <header className="section-header">
          <h2>Добавление профиля</h2>
          {createEmployee.isError && <span className="error">Проверьте введенные данные</span>}
          {createEmployee.isSuccess && <span className="success">Сотрудник добавлен</span>}
        </header>
        <form className="form-grid" onSubmit={handleSubmit}>
          <input placeholder="ID пользователя" value={form.user} onChange={(e) => setForm({ ...form, user: e.target.value })} />
          <input placeholder="ФИО" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
          <input placeholder="ID отдела" value={form.department} onChange={(e) => setForm({ ...form, department: e.target.value })} />
          <input placeholder="ID должности" value={form.position} onChange={(e) => setForm({ ...form, position: e.target.value })} />
          <input placeholder="ID роли" value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })} />
          <button type="submit" disabled={createEmployee.isPending}>Сохранить</button>
        </form>
      </section>

      <section>
        <header className="section-header">
          <h2>Список сотрудников</h2>
        </header>
        <DataTable
          data={employees}
          columns={[
            { header: 'ID', render: (row) => row.id },
            { header: 'ФИО', render: (row) => row.full_name },
            { header: 'Статус', render: (row) => row.status },
            { header: 'Должность', render: (row) => row.position ?? '—' },
            { header: 'Отдел', render: (row) => row.department ?? '—' },
          ]}
        />
      </section>
    </div>
  );
};

export default StaffPage;

