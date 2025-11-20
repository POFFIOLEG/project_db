import { NavLink, Outlet } from 'react-router-dom';

const menu = [
  { to: '/', label: 'Дашборд' },
  { to: '/inventory', label: 'Товарный учет' },
  { to: '/pricing', label: 'Ценообразование' },
  { to: '/staff', label: 'Сотрудники' },
  { to: '/attendance', label: 'Учет времени' },
  { to: '/references', label: 'Справочники' },
];

export const Layout = () => (
  <div className="app-shell">
    <aside className="sidebar">
      <div className="logo">Retail Control</div>
      <nav>
        {menu.map((item) => (
          <NavLink key={item.to} to={item.to} className={({ isActive }) => (isActive ? 'link active' : 'link')}>
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
    <main className="content">
      <Outlet />
    </main>
  </div>
);

