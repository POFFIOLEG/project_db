import { useQuery } from '@tanstack/react-query';

import { DataTable } from '../components/DataTable';
import { StatCard } from '../components/StatCard';
import { fetchList } from '../api';
import type { AttendanceReport, PriceListItem, Product, StockItem } from '../types';

const Dashboard = () => {
  const { data: products = [] } = useQuery({
    queryKey: ['products'],
    queryFn: () => fetchList<Product>('products/'),
  });

  const { data: stock = [] } = useQuery({
    queryKey: ['stock-items'],
    queryFn: () => fetchList<StockItem>('stock-items/'),
  });

  const { data: priceLists = [] } = useQuery({
    queryKey: ['price-lists'],
    queryFn: () => fetchList<PriceListItem>('price-lists/'),
  });

  const { data: attendanceReports = [] } = useQuery({
    queryKey: ['attendance-reports'],
    queryFn: () => fetchList<AttendanceReport>('attendance-reports/'),
  });

  return (
    <div className="page">
      <h1>Обзор магазина</h1>
      <div className="grid">
        <StatCard title="Товаров в каталоге" value={products.length} subtitle="актуальные карточки" />
        <StatCard title="Позиции на складе" value={stock.length} subtitle="учитываются партии" />
        <StatCard title="Прайс-листы" value={priceLists.length} subtitle="регистрация цен" />
        <StatCard title="Отчёты по времени" value={attendanceReports.length} subtitle="зафиксировано недель" />
      </div>

      <section>
        <header className="section-header">
          <h2>Последние остатки</h2>
        </header>
        <DataTable
          data={stock.slice(0, 5)}
          columns={[
            { header: 'Товар', render: (row) => row.product?.name ?? row.product },
            { header: 'Количество', render: (row) => row.quantity },
            { header: 'Зона', render: (row) => row.stock_area },
            { header: 'Годен до', render: (row) => new Date(row.expiration_date).toLocaleDateString() },
          ]}
        />
      </section>

      <section>
        <header className="section-header">
          <h2>Цены на сегодня</h2>
        </header>
        <DataTable
          data={priceLists.slice(0, 5)}
          columns={[
            { header: 'Товар', render: (row) => row.product_name || row.product },
            { header: 'Тип', render: (row) => row.price_type },
            { header: 'Цена', render: (row) => `${row.final_price} ₽` },
            { header: 'Ценник', render: (row) => row.label_type },
          ]}
        />
      </section>
    </div>
  );
};

export default Dashboard;

