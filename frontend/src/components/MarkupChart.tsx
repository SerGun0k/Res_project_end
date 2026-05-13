import type { CostEstimate } from '../types';

export default function MarkupChart({ cost, marketPrice }: { cost: CostEstimate; marketPrice: number }) {
  const markup = marketPrice - cost.total;
  const total = marketPrice;
  const matPct = (cost.materials_cost / total) * 100;
  const logPct = (cost.logistics_cost / total) * 100;
  const laborPct = (cost.labor_cost / total) * 100;
  const markupPct = (markup / total) * 100;

  return (
    <div className="space-y-3">
      <div className="flex rounded-lg overflow-hidden h-6 text-xs font-medium text-white">
        <div style={{ width: `${matPct}%` }} className="bg-blue-500 flex items-center justify-center">
          {matPct > 8 && 'Материалы'}
        </div>
        <div style={{ width: `${logPct}%` }} className="bg-amber-500 flex items-center justify-center">
          {logPct > 8 && 'Логистика'}
        </div>
        <div style={{ width: `${laborPct}%` }} className="bg-emerald-500 flex items-center justify-center">
          {laborPct > 8 && 'Труд'}
        </div>
        <div style={{ width: `${markupPct}%` }} className="bg-red-400 flex items-center justify-center">
          {markupPct > 8 && 'Наценка'}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 bg-blue-500 rounded"></span>
          <span>Материалы: {cost.materials_cost.toLocaleString('ru-RU')} RUB</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 bg-amber-500 rounded"></span>
          <span>Логистика: {cost.logistics_cost.toLocaleString('ru-RU')} RUB</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 bg-emerald-500 rounded"></span>
          <span>Труд: {cost.labor_cost.toLocaleString('ru-RU')} RUB</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 bg-red-400 rounded"></span>
          <span>Наценка: {markup.toLocaleString('ru-RU')} RUB</span>
        </div>
      </div>
    </div>
  );
}
