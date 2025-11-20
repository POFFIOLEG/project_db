import { useState } from 'react';
import type { FormEvent } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { createItem, fetchList } from '../api';
import { DataTable } from '../components/DataTable';
import type { PriceListItem } from '../types';

const blankPrice = {
  product: '',
  stock_area: '',
  price_type: 'regular',
  input_price: '',
  final_price: '',
  regular_price: '',
  label_type: 'white',
  trading_point: 'МХ-001',
  valid_from: new Date().toISOString().slice(0, 10),
};

const PricingPage = () => {
  const queryClient = useQueryClient();
  const [priceForm, setPriceForm] = useState(blankPrice);

  const { data: priceLists = [] } = useQuery({
    queryKey: ['price-lists'],
    queryFn: () => fetchList<PriceListItem>('price-lists/'),
  });

  const { data: stopList = [] } = useQuery({
    queryKey: ['stop-list'],
    queryFn: () => fetchList<{ product: number; trading_point: string; reason: string; blocked_price: string }>(
      'stop-list/',
    ),
  });

  const savePrice = useMutation({
    mutationFn: (payload: Record<string, unknown>) => createItem('price-lists/', payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['price-lists'] });
      setPriceForm(blankPrice);
    },
  });

  const handlePriceSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!priceForm.product || !priceForm.input_price || !priceForm.final_price) return;
    savePrice.mutate({
      ...priceForm,
      product: Number(priceForm.product),
      stock_area: priceForm.stock_area ? Number(priceForm.stock_area) : null,
    });
  };

  return (
    <div className="page">
      <h1>Ценообразование</h1>

      <section>
        <header className="section-header">
          <h2>Цена на товар</h2>
          {savePrice.isError && <span className="error">Проверьте ограничения по цене</span>}
          {savePrice.isSuccess && <span className="success">Цена сохранена</span>}
        </header>
        <form className="form-grid" onSubmit={handlePriceSubmit}>
          <input
            placeholder="ID товара"
            value={priceForm.product}
            onChange={(e) => setPriceForm({ ...priceForm, product: e.target.value })}
          />
          <input
            placeholder="ID зоны (опционально)"
            value={priceForm.stock_area}
            onChange={(e) => setPriceForm({ ...priceForm, stock_area: e.target.value })}
          />
          <select
            value={priceForm.price_type}
            onChange={(e) => setPriceForm({ ...priceForm, price_type: e.target.value })}
          >
            <option value="regular">Регулярная</option>
            <option value="markdown">Уценка</option>
            <option value="promo">Акция</option>
          </select>
          <input
            placeholder="Входная цена"
            value={priceForm.input_price}
            onChange={(e) => setPriceForm({ ...priceForm, input_price: e.target.value })}
          />
          <input
            placeholder="Финальная цена"
            value={priceForm.final_price}
            onChange={(e) => setPriceForm({ ...priceForm, final_price: e.target.value })}
          />
          <input
            placeholder="Регулярная цена"
            value={priceForm.regular_price}
            onChange={(e) => setPriceForm({ ...priceForm, regular_price: e.target.value })}
          />
          <select
            value={priceForm.label_type}
            onChange={(e) => setPriceForm({ ...priceForm, label_type: e.target.value })}
          >
            <option value="white">Белый</option>
            <option value="yellow">Жёлтый</option>
            <option value="promo">Акционный</option>
          </select>
          <button type="submit" disabled={savePrice.isPending}>
            Сохранить
          </button>
        </form>
      </section>

      <section>
        <header className="section-header">
          <h2>Текущие прайсы</h2>
        </header>
        <DataTable
          data={priceLists}
          columns={[
            { header: 'ID', render: (row) => row.id },
            { header: 'Товар', render: (row) => row.product_name || row.product },
            { header: 'Тип', render: (row) => row.price_type },
            { header: 'Цена', render: (row) => `${row.final_price} ₽` },
            { header: 'Ценник', render: (row) => row.label_type },
          ]}
        />
      </section>

      <section>
        <header className="section-header">
          <h2>Стоп-лист направленный в ГК</h2>
        </header>
        <DataTable
          data={stopList}
          columns={[
            { header: 'Товар', render: (row) => row.product },
            { header: 'ТТ', render: (row) => row.trading_point },
            { header: 'Причина', render: (row) => row.reason },
            { header: 'Блок. цена', render: (row) => `${row.blocked_price} ₽` },
          ]}
        />
      </section>
    </div>
  );
};

export default PricingPage;

