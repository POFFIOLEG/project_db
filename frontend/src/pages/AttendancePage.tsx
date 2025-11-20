import { useState } from 'react';
import type { FormEvent } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { createItem, fetchList } from '../api';
import { DataTable } from '../components/DataTable';

interface WorkSession {
  id: number;
  employee: number;
  started_at: string;
  ended_at: string;
}

interface LeaveRequest {
  id: number;
  employee: number;
  leave_type: string;
  start_date: string;
  end_date: string;
  documents_provided: boolean;
}

const AttendancePage = () => {
  const queryClient = useQueryClient();

  const [sessionForm, setSessionForm] = useState({
    employee: '',
    started_at: '',
    ended_at: '',
  });

  const [leaveForm, setLeaveForm] = useState({
    employee: '',
    leave_type: 'vacation',
    start_date: '',
    end_date: '',
  });

  const { data: sessions = [] } = useQuery({
    queryKey: ['work-sessions'],
    queryFn: () => fetchList<WorkSession>('work-sessions/'),
  });

  const { data: leaves = [] } = useQuery({
    queryKey: ['leave-requests'],
    queryFn: () => fetchList<LeaveRequest>('leave-requests/'),
  });

  const createSession = useMutation({
    mutationFn: (payload: Record<string, unknown>) => createItem('work-sessions/', payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['work-sessions'] });
      setSessionForm({ employee: '', started_at: '', ended_at: '' });
    },
  });

  const createLeave = useMutation({
    mutationFn: (payload: Record<string, unknown>) => createItem('leave-requests/', payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['leave-requests'] });
      setLeaveForm({ employee: '', leave_type: 'vacation', start_date: '', end_date: '' });
    },
  });

  const handleSessionSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!sessionForm.employee || !sessionForm.started_at) return;
    createSession.mutate({
      ...sessionForm,
      employee: Number(sessionForm.employee),
    });
  };

  const handleLeaveSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!leaveForm.employee || !leaveForm.start_date || !leaveForm.end_date) return;
    createLeave.mutate({
      ...leaveForm,
      employee: Number(leaveForm.employee),
    });
  };

  return (
    <div className="page">
      <h1>Учёт рабочего времени</h1>

      <section>
        <header className="section-header">
          <h2>Фиксация смены</h2>
        </header>
        <form className="form-grid" onSubmit={handleSessionSubmit}>
          <input
            placeholder="ID сотрудника"
            value={sessionForm.employee}
            onChange={(e) => setSessionForm({ ...sessionForm, employee: e.target.value })}
          />
          <input
            type="datetime-local"
            value={sessionForm.started_at}
            onChange={(e) => setSessionForm({ ...sessionForm, started_at: e.target.value })}
          />
          <input
            type="datetime-local"
            value={sessionForm.ended_at}
            onChange={(e) => setSessionForm({ ...sessionForm, ended_at: e.target.value })}
          />
          <button type="submit" disabled={createSession.isPending}>
            Сохранить
          </button>
        </form>
      </section>

      <section>
        <header className="section-header">
          <h2>Запрос отпуска/больничного</h2>
        </header>
        <form className="form-grid" onSubmit={handleLeaveSubmit}>
          <input
            placeholder="ID сотрудника"
            value={leaveForm.employee}
            onChange={(e) => setLeaveForm({ ...leaveForm, employee: e.target.value })}
          />
          <select value={leaveForm.leave_type} onChange={(e) => setLeaveForm({ ...leaveForm, leave_type: e.target.value })}>
            <option value="vacation">Отпуск</option>
            <option value="sick">Больничный</option>
            <option value="unpaid">Без содержания</option>
          </select>
          <input type="date" value={leaveForm.start_date} onChange={(e) => setLeaveForm({ ...leaveForm, start_date: e.target.value })} />
          <input type="date" value={leaveForm.end_date} onChange={(e) => setLeaveForm({ ...leaveForm, end_date: e.target.value })} />
          <button type="submit" disabled={createLeave.isPending}>
            Отправить
          </button>
        </form>
      </section>

      <section>
        <header className="section-header">
          <h2>Последние смены</h2>
        </header>
        <DataTable
          data={sessions.slice(0, 10)}
          columns={[
            { header: 'Сотрудник', render: (row) => row.employee },
            { header: 'Начало', render: (row) => new Date(row.started_at).toLocaleString() },
            { header: 'Окончание', render: (row) => (row.ended_at ? new Date(row.ended_at).toLocaleString() : '—') },
          ]}
        />
      </section>

      <section>
        <header className="section-header">
          <h2>Заявки</h2>
        </header>
        <DataTable
          data={leaves.slice(0, 10)}
          columns={[
            { header: 'Сотрудник', render: (row) => row.employee },
            { header: 'Тип', render: (row) => row.leave_type },
            { header: 'Период', render: (row) => `${row.start_date} → ${row.end_date}` },
            { header: 'Документы', render: (row) => (row.documents_provided ? 'есть' : 'нет') },
          ]}
        />
      </section>
    </div>
  );
};

export default AttendancePage;

