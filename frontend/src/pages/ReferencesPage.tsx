import { useState } from 'react';
import type { FormEvent } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { createItem, fetchList } from '../api';
import { DataTable } from '../components/DataTable';

interface Country {
  id: number;
  code: string;
  name: string;
}

interface Supplier {
  id: number;
  name: string;
  phone: string;
  email: string;
  country: Country | number;
}

interface StorageLocation {
  id: number;
  code: string;
  name: string;
  location_type: string;
}

const ReferencesPage = () => {
  const queryClient = useQueryClient();

  const [countryForm, setCountryForm] = useState({ code: '', name: '' });
  const [supplierForm, setSupplierForm] = useState({ name: '', phone: '', email: '', country: '' });
  const [storageForm, setStorageForm] = useState({ code: '', name: '', location_type: 'warehouse' });

  const { data: countries = [] } = useQuery({
    queryKey: ['countries'],
    queryFn: () => fetchList<Country>('countries/'),
  });

  const { data: suppliers = [] } = useQuery({
    queryKey: ['suppliers'],
    queryFn: () => fetchList<Supplier>('suppliers/'),
  });

  const { data: storages = [] } = useQuery({
    queryKey: ['storage-locations'],
    queryFn: () => fetchList<StorageLocation>('storage-locations/'),
  });

  const createCountry = useMutation({
    mutationFn: (payload: typeof countryForm) => createItem('countries/', payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['countries'] });
      setCountryForm({ code: '', name: '' });
    },
  });

  const createSupplier = useMutation({
    mutationFn: (payload: Record<string, unknown>) => createItem('suppliers/', payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['suppliers'] });
      setSupplierForm({ name: '', phone: '', email: '', country: '' });
    },
  });

  const createStorage = useMutation({
    mutationFn: (payload: typeof storageForm) => createItem('storage-locations/', payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['storage-locations'] });
      setStorageForm({ code: '', name: '', location_type: 'warehouse' });
    },
  });

  const handleCountrySubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!countryForm.code || !countryForm.name) return;
    createCountry.mutate(countryForm);
  };

  const handleSupplierSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!supplierForm.name || !supplierForm.country) return;
    createSupplier.mutate({
      name: supplierForm.name,
      phone: supplierForm.phone,
      email: supplierForm.email,
      country_id: Number(supplierForm.country),
    });
  };

  const handleStorageSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!storageForm.code || !storageForm.name) return;
    createStorage.mutate(storageForm);
  };

  return (
    <div className="page">
      <h1>Справочники</h1>

      <section>
        <header className="section-header">
          <h2>Страны</h2>
        </header>
        <form className="form-inline" onSubmit={handleCountrySubmit}>
          <input placeholder="Код" value={countryForm.code} onChange={(e) => setCountryForm({ ...countryForm, code: e.target.value })} />
          <input placeholder="Название" value={countryForm.name} onChange={(e) => setCountryForm({ ...countryForm, name: e.target.value })} />
          <button type="submit" disabled={createCountry.isPending}>Добавить</button>
        </form>
        <DataTable
          data={countries}
          columns={[
            { header: 'Код', render: (row) => row.code },
            { header: 'Название', render: (row) => row.name },
          ]}
        />
      </section>

      <section>
        <header className="section-header">
          <h2>Поставщики</h2>
        </header>
        <form className="form-grid" onSubmit={handleSupplierSubmit}>
          <input placeholder="Название" value={supplierForm.name} onChange={(e) => setSupplierForm({ ...supplierForm, name: e.target.value })} />
          <input placeholder="Телефон" value={supplierForm.phone} onChange={(e) => setSupplierForm({ ...supplierForm, phone: e.target.value })} />
          <input placeholder="Email" value={supplierForm.email} onChange={(e) => setSupplierForm({ ...supplierForm, email: e.target.value })} />
          <input placeholder="ID страны" value={supplierForm.country} onChange={(e) => setSupplierForm({ ...supplierForm, country: e.target.value })} />
          <button type="submit" disabled={createSupplier.isPending}>Сохранить</button>
        </form>
        <DataTable
          data={suppliers}
          columns={[
            { header: 'Название', render: (row) => row.name },
            { header: 'Телефон', render: (row) => row.phone || '—' },
            { header: 'Email', render: (row) => row.email || '—' },
            {
              header: 'Страна',
              render: (row) => (typeof row.country === 'object' ? row.country?.name : row.country ?? '—'),
            },
          ]}
        />
      </section>

      <section>
        <header className="section-header">
          <h2>Места хранения</h2>
        </header>
        <form className="form-grid" onSubmit={handleStorageSubmit}>
          <input placeholder="Код" value={storageForm.code} onChange={(e) => setStorageForm({ ...storageForm, code: e.target.value })} />
          <input placeholder="Название" value={storageForm.name} onChange={(e) => setStorageForm({ ...storageForm, name: e.target.value })} />
          <select value={storageForm.location_type} onChange={(e) => setStorageForm({ ...storageForm, location_type: e.target.value })}>
            <option value="warehouse">Склад</option>
            <option value="shop_floor">Торговый зал</option>
            <option value="dc">Распред. центр</option>
            <option value="hq">ГК</option>
          </select>
          <button type="submit" disabled={createStorage.isPending}>Сохранить</button>
        </form>
        <DataTable
          data={storages}
          columns={[
            { header: 'Код', render: (row) => row.code },
            { header: 'Название', render: (row) => row.name },
            { header: 'Тип', render: (row) => row.location_type },
          ]}
        />
      </section>
    </div>
  );
};

export default ReferencesPage;

