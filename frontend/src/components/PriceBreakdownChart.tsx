import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import type { PriceHistory } from '../types';

interface PriceBreakdownChartProps {
  prices: PriceHistory[];
  costEstimate?: {
    materials_cost: number;
    logistics_cost: number;
    labor_cost: number;
    total: number;
  };
}

const COLORS = ['#3b82f6', '#f59e0b', '#10b981', '#ef4444'];

export default function PriceBreakdownChart({ prices, costEstimate }: PriceBreakdownChartProps) {
  if (!costEstimate) {
    return <p className="text-sm text-slate-500">Нет данных о себестоимости</p>;
  }

  // Данные для круговой диаграммы
  const marketPrice = prices.length > 0
    ? prices.reduce((s, p) => s + p.price, 0) / prices.length
    : costEstimate.total;

  const markup = Math.max(0, marketPrice - costEstimate.total);

  const data = [
    { name: 'Материалы', value: costEstimate.materials_cost },
    { name: 'Логистика', value: costEstimate.logistics_cost },
    { name: 'Труд', value: costEstimate.labor_cost },
    { name: 'Наценка', value: markup },
  ];

  return (
    <div className="space-y-4">
      {/* Краткая статистика */}
      <div className="grid grid-cols-2 gap-3 text-sm">
        <div className="bg-slate-50 rounded-lg p-3 text-center">
          <p className="text-lg font-bold text-slate-900">{marketPrice.toLocaleString('ru-RU', { maximumFractionDigits: 0 })} ₽</p>
          <p className="text-slate-500 text-xs">Средняя рыночная</p>
        </div>
        <div className="bg-slate-50 rounded-lg p-3 text-center">
          <p className="text-lg font-bold text-slate-900">{costEstimate.total.toLocaleString('ru-RU')} ₽</p>
          <p className="text-slate-500 text-xs">Себестоимость</p>
        </div>
      </div>

      {/* Круговая диаграмма */}
      <div className="w-full h-64 pointer-events-none select-none">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, percent }) => `${name} ${percent ? (percent * 100).toFixed(0) : 0}%`}
              outerRadius={80}
              fill="#8884d8"
              dataKey="value"
              isAnimationActive={false}
            >
              {data.map((_entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} style={{ pointerEvents: 'none' }} />
              ))}
            </Pie>
            <Tooltip
              formatter={(value) => {
                if (typeof value === 'number') return `${value.toLocaleString('ru-RU')} ₽`;
                return String(value ?? '');
              }}
            />
            <Legend wrapperStyle={{ pointerEvents: 'none' }} />
          </PieChart>
        </ResponsiveContainer>
      </div>

      {/* Легенда с расшифровкой */}
      <div className="grid grid-cols-2 gap-2 text-xs">
        {data.map((item, i) => (
          <div key={item.name} className="flex items-center gap-2">
            <span className="w-3 h-3 rounded" style={{ backgroundColor: COLORS[i] }}></span>
            <span className="text-slate-600">{item.name}: {item.value.toLocaleString('ru-RU')} ₽</span>
          </div>
        ))}
      </div>
    </div>
  );
}
