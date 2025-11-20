import { Route, Routes } from 'react-router-dom';

import './App.css';
import { Layout } from './components/Layout';
import AttendancePage from './pages/AttendancePage';
import Dashboard from './pages/Dashboard';
import InventoryPage from './pages/InventoryPage';
import PricingPage from './pages/PricingPage';
import ReferencesPage from './pages/ReferencesPage';
import StaffPage from './pages/StaffPage';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="inventory" element={<InventoryPage />} />
        <Route path="pricing" element={<PricingPage />} />
        <Route path="staff" element={<StaffPage />} />
        <Route path="attendance" element={<AttendancePage />} />
        <Route path="references" element={<ReferencesPage />} />
      </Route>
    </Routes>
  );
}

export default App;
