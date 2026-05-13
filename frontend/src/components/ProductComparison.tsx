import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import type { ProductWithMarkup } from '../types';
import { getProductImage } from '../utils/images';

interface ProductComparisonProps {
  products: ProductWithMarkup[];
  onRemove: (id: number) => void;
}

interface SpecRow {
  label: string;
  values: (string | number | null)[];
  lowerIsBetter?: boolean;
}

export default function ProductComparison({ products, onRemove }: ProductComparisonProps) {
  const [specRows, setSpecRows] = useState<SpecRow[]>([]);

  useEffect(() => {
    if (products.length < 2) return;

    const rows: SpecRow[] = [];

    // Цена
    rows.push({
      label: 'Цена, ₽',
      values: products.map((p) => p.market_price),
      lowerIsBetter: true,
    });

    // Себестоимость
    rows.push({
      label: 'Себестоимость, ₽',
      values: products.map((p) => p.cost_estimate?.total ?? null),
      lowerIsBetter: true,
    });

    // Наценка
    rows.push({
      label: 'Наценка, %',
      values: products.map((p) => p.markup_percent),
      lowerIsBetter: true,
    });

    // Рейтинг
    rows.push({
      label: 'Рейтинг',
      values: products.map((p) => p.review_quality?.avg_rating ?? null),
      lowerIsBetter: false,
    });

    // Характеристики из specs
    if (products[0]?.specs) {
      const allKeys = new Set<string>();
      products.forEach((p) => {
        if (p.specs) Object.keys(p.specs).forEach((k) => allKeys.add(k));
      });

      allKeys.forEach((key) => {
        const label = specKeyToLabel(key);
        const values = products.map((p) => {
          const val = p.specs?.[key];
          if (val === undefined || val === null) return null;
          if (typeof val === 'object') return JSON.stringify(val);
          return String(val);
        });

        // Числовые параметры — lowerIsBetter если это TDP, noise и т.п.
        const lowerIsBetterKeys = ['tdp_watts', 'noise_dba'];
        rows.push({
          label,
          values,
          lowerIsBetter: lowerIsBetterKeys.includes(key),
        });
      });
    }

    setSpecRows(rows);
  }, [products]);

  if (products.length < 2) {
    return (
      <div className="text-center py-8 bg-slate-50 dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700">
        <p className="text-slate-500 dark:text-slate-400">
          Выберите 2-3 товара для сравнения. Нажмите «Сравнить» на карточках товаров.
        </p>
      </div>
    );
  }

  // Находим лучшие значения для подсветки
  const getBestIndex = (row: SpecRow): number | null => {
    const numericValues = row.values
      .map((v, i) => ({ v: typeof v === 'number' ? v : null, i }))
      .filter((x) => x.v !== null);

    if (numericValues.length < 2) return null;

    if (row.lowerIsBetter) {
      const min = Math.min(...numericValues.map((x) => x.v!));
      return numericValues.find((x) => x.v === min)!.i;
    } else {
      const max = Math.max(...numericValues.map((x) => x.v!));
      return numericValues.find((x) => x.v === max)!.i;
    }
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr>
            <th className="text-left p-3 bg-slate-50 dark:bg-slate-900 border-b border-slate-200 dark:border-slate-700 font-semibold text-slate-700 dark:text-slate-300 w-40">
              Характеристика
            </th>
            {products.map((product) => {
              const imgUrl = getProductImage(
                product.category,
                product.brand,
                product.model,
                120,
                (product.specs as any)?.image_url,
              );
              return (
                <th key={product.id} className="p-3 border-b border-slate-200 dark:border-slate-700 min-w-48">
                  <div className="flex flex-col items-center gap-2">
                    <div className="relative">
                      <div className="w-24 h-24 bg-slate-50 dark:bg-slate-800 rounded-lg flex items-center justify-center p-2">
                        <img
                          src={imgUrl}
                          alt={`${product.brand} ${product.model}`}
                          className="max-w-full max-h-full object-contain"
                        />
                      </div>
                      <button
                        onClick={() => onRemove(product.id)}
                        className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white rounded-full text-xs flex items-center justify-center hover:bg-red-600"
                        title="Убрать из сравнения"
                      >
                        ×
                      </button>
                    </div>
                    <Link
                      to={`/product/${product.category}/${product.id}`}
                      className="font-semibold text-slate-900 dark:text-slate-100 hover:text-blue-600 dark:hover:text-blue-400 text-center"
                    >
                      {product.brand} {product.model}
                    </Link>
                    {product.market_price && (
                      <span className="text-base font-bold text-slate-900 dark:text-slate-100">
                        {product.market_price.toLocaleString('ru-RU')} ₽
                      </span>
                    )}
                  </div>
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody>
          {specRows.map((row, idx) => {
            const bestIdx = getBestIndex(row);
            return (
              <tr
                key={idx}
                className={idx % 2 === 0 ? 'bg-white dark:bg-slate-950' : 'bg-slate-50 dark:bg-slate-900'}
              >
                <td className="p-3 font-medium text-slate-700 dark:text-slate-300 border-b border-slate-100 dark:border-slate-800">
                  {row.label}
                </td>
                {row.values.map((val, i) => (
                  <td
                    key={i}
                    className={`p-3 text-center border-b border-slate-100 dark:border-slate-800 ${
                      i === bestIdx
                        ? 'bg-green-100 dark:bg-green-900/40 text-green-800 dark:text-green-200 font-bold'
                        : 'text-slate-700 dark:text-slate-300'
                    }`}
                  >
                    {val !== null && val !== undefined ? (
                      typeof val === 'number' ? (
                        val.toLocaleString('ru-RU', { maximumFractionDigits: 1 })
                      ) : (
                        String(val)
                      )
                    ) : (
                      <span className="text-slate-400">—</span>
                    )}
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// Маппинг ключей specs → человекочитаемые названия
function specKeyToLabel(key: string): string {
  const map: Record<string, string> = {
    memory_gb: 'Объём памяти, ГБ',
    memory_type: 'Тип памяти',
    tdp_watts: 'TDP, Вт',
    cores: 'Ядра',
    threads: 'Потоки',
    base_clock_ghz: 'Базовая частота, ГГц',
    boost_clock_ghz: 'Турбо частота, ГГц',
    socket: 'Сокет',
    capacity_gb: 'Объём, ГБ',
    type: 'Тип',
    speed_mhz: 'Частота, МГц',
    interface: 'Интерфейс',
    read_mbps: 'Чтение, МБ/с',
    write_mbps: 'Запись, МБ/с',
    rpm: 'Обороты, об/мин',
    cache_mb: 'Кэш, МБ',
    watts: 'Мощность, Вт',
    efficiency: 'Эффективность',
    modular: 'Модульный',
    noise_dba: 'Уровень шума, дБА',
    connector: 'Разъём',
  };
  return map[key] || key;
}
