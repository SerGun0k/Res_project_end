import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import SearchBar from '../components/SearchBar';
import { productsApi } from '../api/products';
import { getProductImage } from '../utils/images';
import type { DailyProductItem } from '../types';

export default function HomePage() {
  const [dailyProducts, setDailyProducts] = useState<DailyProductItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    productsApi.getDaily(5)
      .then((res) => {
        console.log('Daily products:', res.data.products.length);
        setDailyProducts(res.data.products);
      })
      .catch((err) => {
        console.error('Failed to load daily products:', err);
        setDailyProducts([]);
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-12">
      {/* Hero */}
      <section className="text-center py-12">
        <h1 className="text-4xl font-bold text-slate-900 dark:text-slate-100">Оценка цен на компьютерные комплектующие</h1>
        <p className="mt-4 text-lg text-slate-600 dark:text-slate-400 max-w-2xl mx-auto">
          Сравните себестоимость и рыночную цену. Узнайте, обоснована ли наценка, и найдите аналоги с лучшим соотношением цена/качество.
        </p>
        <div className="mt-8 flex justify-center">
          <SearchBar />
        </div>
      </section>

      {/* Быстрые категории */}
      <section>
        <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-6">Категории</h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { label: 'Видеокарты', cat: 'GPU' },
            { label: 'Процессоры', cat: 'CPU' },
            { label: 'Оперативная память', cat: 'RAM' },
            { label: 'Накопители', cat: 'SSD', sub: ['M2', 'SATA', 'NVMe'] },
            { label: 'Жёсткие диски', cat: 'HDD' },
            { label: 'Блоки питания', cat: 'PSU' },
            { label: 'Охлаждение', cat: 'COOLING' },
          ].map((item) => (
            <div key={item.cat} className="space-y-1">
              <Link
                to={`/search?cat=${item.cat}`}
                className="flex flex-col items-center gap-2 p-4 border border-slate-200 dark:border-slate-700 rounded-lg hover:shadow-md transition group block bg-white dark:bg-slate-900"
              >
                <div className="w-12 h-12 flex items-center justify-center">
                  <span className="text-2xl font-bold text-slate-700 dark:text-slate-300 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition">{item.cat}</span>
                </div>
                <span className="text-sm font-medium text-slate-700 dark:text-slate-300">{item.label}</span>
              </Link>
              {'sub' in item && item.sub && (
                <div className="flex flex-wrap justify-center gap-1 px-2">
                  {item.sub.map((sub) => (
                    <Link
                      key={sub}
                      to={`/search?cat=${item.cat}&sub=${sub}`}
                      className="text-xs text-slate-500 dark:text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 transition"
                    >
                      {sub}
                    </Link>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* Товары дня */}
      <section>
        <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-6">Товары дня</h2>
        {loading ? (
          <p className="text-slate-500 dark:text-slate-400">Загрузка...</p>
        ) : dailyProducts.length === 0 ? (
          <p className="text-slate-500 dark:text-slate-400">Нет данных. Запустите <code className="bg-slate-100 dark:bg-slate-800 px-1 rounded">docker-compose exec backend python data_pipeline/clean_and_seed.py</code></p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
            {dailyProducts.map((item) => {
              const imgUrl = getProductImage(
                item.product.category,
                item.product.brand,
                item.product.model,
                200,
                (item.product.specs as any)?.image_url,
              );
              const url = `/product/${item.product.category}/${item.product.id}`;
              return (
                <Link
                  key={item.product.id}
                  to={url}
                  className="block border border-slate-200 dark:border-slate-700 rounded-lg overflow-hidden hover:shadow-md transition bg-white dark:bg-slate-900"
                >
                  <div className="aspect-[4/3] bg-slate-50 dark:bg-slate-800 flex items-center justify-center p-4">
                    <img
                      src={imgUrl}
                      alt={`${item.product.brand} ${item.product.model}`}
                      className="max-w-full max-h-full object-contain"
                    />
                  </div>
                  <div className="p-3">
                    <p className="text-xs text-slate-500 dark:text-slate-400">{item.product.category}</p>
                    <p className="font-semibold text-sm text-slate-900 dark:text-slate-100 mt-1">{item.product.brand} {item.product.model}</p>
                    <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
                      {item.avg_price.toLocaleString('ru-RU')} ₽
                    </p>
                    <p className="text-xs text-slate-500 dark:text-slate-500 mt-1">
                      {item.daily_views} просм./день
                    </p>
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
