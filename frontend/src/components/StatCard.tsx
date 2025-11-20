interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
}

export const StatCard = ({ title, value, subtitle }: StatCardProps) => (
  <div className="stat-card">
    <p className="stat-title">{title}</p>
    <p className="stat-value">{value}</p>
    {subtitle && <p className="stat-subtitle">{subtitle}</p>}
  </div>
);

