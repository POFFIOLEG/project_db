import { useState } from 'react';
import type { FormEvent } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { createItem, fetchList } from '../api';
import { DataTable } from '../components/DataTable';
import type { Product, StockItem } from '../types';

const blankProduct = {
  name: '',
  sku: '',
  barcode: '',
  manufacturer: '',
  country: '',
  unit: 'pcs',
  shelf_life_days: '0',
};

const InventoryPage = () => {
  const queryClient = useQueryClient();
  const [form, setForm] = useState(blankProduct);

  const { data: products = [] } = useQuery({
    queryKey: ['products'],
    queryFn: () => fetchList<Product>('products/'),
  });

  const { data: stockItems = [] } = useQuery({
    queryKey: ['stock-items'],
    queryFn: () => fetchList<StockItem>('stock-items/'),
  });

  const createProduct = useMutation({
    mutationFn: (payload: Record<string, unknown>) => createItem('products/', payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] });
      setForm(blankProduct);
    },
  });

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!form.name || !form.manufacturer || !form.country) return;
    createProduct.mutate({
      ...form,
      shelf_life_days: Number(form.shelf_life_days),
    });
  };

  return (
    <div className="page">
      <h1>Товарный учет</h1>

      <section>
        <header className="section-header">
          <div>
            <h2>Новая карточка товара</h2>
            <p>Заполните обязательные поля и ID страны/производителя</p>
          </div>
          {createProduct.isError && <span className="error">Не удалось сохранить карточку</span>}
          {createProduct.isSuccess && <span className="success">Карточка создана</span>}
        </header>
        <form className="form-grid" onSubmit={handleSubmit}>
          <input placeholder="Название" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <input placeholder="SKU" value={form.sku} onChange={(e) => setForm({ ...form, sku: e.target.value })} />
          <input
            placeholder="Штрихкод"
            value={form.barcode}
            onChange={(e) => setForm({ ...form, barcode: e.target.value })}
          />
          <input
            placeholder="ID производителя"
            value={form.manufacturer}
            onChange={(e) => setForm({ ...form, manufacturer: e.target.value })}
          />
          <input
            placeholder="ID страны"
            value={form.country}
            onChange={(e) => setForm({ ...form, country: e.target.value })}
          />
          <select value={form.unit} onChange={(e) => setForm({ ...form, unit: e.target.value })}>
            <option value="pcs">шт</option>
            <option value="kg">кг</option>
            <option value="l">л</option>
            <option value="pack">уп</option>
          </select>
          <input type="number" placeholder="Срок годности, дней" value={form.shelf_life_days} onChange={(e) => setForm({ ...form, shelf_life_days: e.target.value })} />
          <button type="submit" disabled={createProduct.isPending}>
            Создать
          </button>
        </form>
      </section>

      <section>
        <header className="section-header">
          <h2>Каталог товаров</h2>
        </header>
        <DataTable
          data={products}
          columns={[
            { header: 'Название', render: (row) => row.name },
            { header: 'SKU', render: (row) => row.sku },
            { header: 'Штрихкод', render: (row) => row.barcode },
            { header: 'Категория', render: (row) => row.category || '—' },
            { header: 'Срок годности', render: (row) => `${row.shelf_life_days} дн.` },
          ]}
        />
      </section>

      <section>
        <header className="section-header">
          <h2>Остатки по зонам</h2>
        </header>
        <DataTable
          data={stockItems}
          columns={[
            { header: 'Товар', render: (row) => row.product?.name ?? row.product },
            { header: 'Кол-во', render: (row) => row.quantity },
            { header: 'Зона', render: (row) => row.stock_area },
            { header: 'Годен до', render: (row) => new Date(row.expiration_date).toLocaleDateString() },
          ]}
        />
      </section>
    </div>
  );
};

export default InventoryPage;

