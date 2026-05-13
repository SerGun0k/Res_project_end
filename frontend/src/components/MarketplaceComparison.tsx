import { useState, useEffect } from 'react';
import api from '../api/client';

interface MarketplacePrice {
  source: string;
  price: number;
  date: string;
  url: string;
  logo: string;
}

interface MarketplacePrices {
  product_id: number;
  product_name: string;
  prices: MarketplacePrice[];
  best_price: number | null;
  best_source: string | null;
  price_diff: number;
}

export default function MarketplaceComparison({ productId }: { productId: number }) {
  const [data, setData] = useState<MarketplacePrices | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get(`/marketplace-prices/${productId}`)
      .then((res) => setData(res.data))
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [productId]);

  if (loading) return <p className="text-sm text-slate-500 dark:text-slate-400">Загрузка цен...</p>;
  if (!data || data.prices.length === 0) {
    return (
      <div className="text-center py-6 bg-slate-50 dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700">
        <p className="text-sm text-slate-600 dark:text-slate-400">
          🔍 Цены по магазинам пока не загружены
        </p>
        <p className="text-xs text-slate-500 dark:text-slate-500 mt-2 max-w-md mx-auto">
          Для отображения реальных цен из DNS, Ozon, Citilink и других магазинов
          необходимо подключить API сборщик цен. Сейчас цены рассчитываются
          на основе себестоимости и наценки.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100">🏪 Где купить дешевле</h3>

      {/* Лучшая цена */}
      {data.best_source && data.best_price !== null && (
        <div className="bg-green-50 dark:bg-green-900/30 border border-green-200 dark:border-green-800 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-green-700 dark:text-green-300 font-medium">
                ✅ Лучшая цена: {data.best_source}
              </p>
              <p className="text-2xl font-bold text-green-800 dark:text-green-200">
                {data.best_price.toLocaleString('ru-RU')} ₽
              </p>
            </div>
            {data.price_diff > 0 && (
              <div className="text-right">
                <p className="text-sm text-green-600 dark:text-green-400">Экономия до</p>
                <p className="text-lg font-bold text-green-700 dark:text-green-300">
                  {data.price_diff.toLocaleString('ru-RU')} ₽
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Таблица цен */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-200 dark:border-slate-700">
              <th className="text-left py-2 px-3 text-slate-600 dark:text-slate-400">Магазин</th>
              <th className="text-right py-2 px-3 text-slate-600 dark:text-slate-400">Цена</th>
              <th className="text-right py-2 px-3 text-slate-600 dark:text-slate-400"></th>
            </tr>
          </thead>
          <tbody>
            {data.prices.map((item, idx) => (
              <tr
                key={item.source}
                className={`border-b border-slate-100 dark:border-slate-800 ${
                  idx === 0 ? 'bg-green-50 dark:bg-green-900/20' : ''
                }`}
              >
                <td className="py-3 px-3">
                  <div className="flex items-center gap-2">
                    <span className="text-lg">{item.logo}</span>
                    <span className="font-medium text-slate-900 dark:text-slate-100">
                      {item.source}
                    </span>
                    {idx === 0 && (
                      <span className="text-xs bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 px-2 py-0.5 rounded-full">
                        Лучшая
                      </span>
                    )}
                  </div>
                </td>
                <td className="py-3 px-3 text-right">
                  <span className={`font-bold ${
                    idx === 0
                      ? 'text-green-700 dark:text-green-300'
                      : 'text-slate-900 dark:text-slate-100'
                  }`}>
                    {item.price.toLocaleString('ru-RU')} ₽
                  </span>
                </td>
                <td className="py-3 px-3 text-right">
                  {item.url && (
                    <a
                      href={item.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 dark:text-blue-400 hover:underline text-xs"
                    >
                      Перейти →
                    </a>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="text-xs text-slate-500 dark:text-slate-400">
        Цены обновлены: {new Date(data.prices[0]?.date).toLocaleDateString('ru-RU')}
      </p>
    </div>
  );
}
