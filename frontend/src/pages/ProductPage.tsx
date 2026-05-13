import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { productsApi } from '../api/products';
import SpecsTable from '../components/SpecsTable';
import AlternativesList from '../components/AlternativesList';
import PriceBreakdownChart from '../components/PriceBreakdownChart';
import MarketplaceComparison from '../components/MarketplaceComparison';
import { getProductImage } from '../utils/images';
import type { ProductFull, AlternativeProduct } from '../types';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

export default function ProductPage() {
  const { category, id } = useParams<{ category: string; id: string }>();
  const navigate = useNavigate();
  const [product, setProduct] = useState<ProductFull | null>(null);
  const [alternatives, setAlternatives] = useState<AlternativeProduct[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;

    Promise.all([
      productsApi.getById(Number(id)),
      productsApi.getAlternatives(Number(id), category || '', 5).catch(() => ({ data: { alternatives: [] } })),
    ])
      .then(([productRes, altRes]) => {
        setProduct(productRes.data);
        setAlternatives(altRes.data.alternatives);

        // Трекинг просмотра
        productsApi.trackView(Number(id)).catch(() => {});
      })
      .catch(() => {
        // Если не нашли — редирект на поиск
        navigate(`/search?q=${id}`);
      })
      .finally(() => setLoading(false));
  }, [id, category, navigate]);

  if (loading) {
    return <p className="text-center text-slate-500 py-12">Загрузка...</p>;
  }

  if (!product) {
    return <p className="text-center text-slate-500 py-12">Товар не найден</p>;
  }

  const medianPrice = product.price_history.length > 0
    ? product.price_history.reduce((sum, p) => sum + p.price, 0) / product.price_history.length
    : 0;

  const markupPercent = product.cost_estimate && medianPrice > 0
    ? ((medianPrice - product.cost_estimate.total) / product.cost_estimate.total * 100).toFixed(1)
    : null;

  const imgUrl = getProductImage(
    product.category,
    product.brand,
    product.model,
    400,
    (product.specs as any)?.image_url,
  );

  return (
    <div className="space-y-8">
      {/* Блок 1: Название + картинка | Характеристики */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Левая часть: Картинка + название */}
        <section className="space-y-4">
          <div className="aspect-square bg-slate-50 dark:bg-slate-900 rounded-lg flex items-center justify-center p-8">
            <img
              src={imgUrl}
              alt={`${product.brand} ${product.model}`}
              className="max-w-full max-h-full object-contain"
            />
          </div>
          <div>
            <p className="text-sm text-slate-500 dark:text-slate-400">{product.category}{product.subcategory ? ` → ${product.subcategory}` : ''}</p>
            <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100">{product.brand} {product.model}</h1>
            {product.release_date && (
              <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                Дата выхода: {new Date(product.release_date).toLocaleDateString('ru-RU')}
              </p>
            )}
          </div>
          {product.specs && <SpecsTable specs={product.specs} />}
        </section>

        {/* Правая часть: Анализ цены */}
        <section className="space-y-6">
          <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100">Анализ цены</h2>

          {product.cost_estimate && (
            <PriceBreakdownChart
              prices={product.price_history}
              costEstimate={product.cost_estimate}
            />
          )}

          <div className="space-y-3 text-sm">
            <div className="flex items-baseline gap-4">
              <span className="text-3xl font-bold text-slate-900 dark:text-slate-100">
                {medianPrice.toLocaleString('ru-RU', { maximumFractionDigits: 0 })} ₽
              </span>
              <span className="text-slate-500 dark:text-slate-400">Средняя рыночная цена</span>
            </div>

            {product.cost_estimate && (
              <div className="flex items-baseline gap-4">
                <span className="text-2xl font-semibold text-slate-700 dark:text-slate-300">
                  {product.cost_estimate.total.toLocaleString('ru-RU')} ₽
                </span>
                <span className="text-slate-500 dark:text-slate-400">Себестоимость</span>
              </div>
            )}

            {markupPercent && (
              <div className="flex items-baseline gap-4">
                <span className={`text-2xl font-bold ${Number(markupPercent) > 40 ? 'text-red-600' : 'text-green-600'}`}>
                  {markupPercent}%
                </span>
                <span className="text-slate-500 dark:text-slate-400">Наценка</span>
                {product.cost_estimate && product.cost_estimate.total > 0 && medianPrice > 0 && (
                  <span className={`text-xs px-2 py-1 rounded-full ${Number(markupPercent) > 40 ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200' : 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'}`}>
                    {Number(markupPercent) > 40 ? 'Завышена' : 'В норме'}
                  </span>
                )}
              </div>
            )}
          </div>
        </section>
      </div>

      {/* Где купить */}
      <section>
        <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 mb-4">Где купить</h2>
        <MarketplaceComparison productId={product.id} />
      </section>

      {/* Отзывы (без источника) */}
      {product.review_quality && (
        <section>
          <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 mb-4">Качество и отзывы</h2>
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div className="bg-slate-50 dark:bg-slate-900 rounded-lg p-4 text-center">
              <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                {product.review_quality.avg_rating?.toFixed(1) ?? '—'}
              </p>
              <p className="text-slate-500 dark:text-slate-400">Рейтинг</p>
            </div>
            <div className="bg-slate-50 dark:bg-slate-900 rounded-lg p-4 text-center">
              <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                {product.review_quality.reviews_count ?? '—'}
              </p>
              <p className="text-slate-500 dark:text-slate-400">Отзывов</p>
            </div>
            <div className="bg-slate-50 dark:bg-slate-900 rounded-lg p-4 text-center">
              <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                {product.review_quality.defect_rate?.toFixed(1) ?? '—'}%
              </p>
              <p className="text-slate-500 dark:text-slate-400">Процент брака</p>
            </div>
          </div>
        </section>
      )}

      {/* Популярность */}
      {product.popularity_stats && (
        <section>
          <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 mb-4">Популярность</h2>
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div className="bg-slate-50 dark:bg-slate-900 rounded-lg p-4 text-center">
              <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">{product.popularity_stats.daily_views}</p>
              <p className="text-slate-500 dark:text-slate-400">Просмотров/день</p>
            </div>
            <div className="bg-slate-50 dark:bg-slate-900 rounded-lg p-4 text-center">
              <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">{product.popularity_stats.total_views.toLocaleString('ru-RU')}</p>
              <p className="text-slate-500 dark:text-slate-400">Всего просмотров</p>
            </div>
            <div className="bg-slate-50 dark:bg-slate-900 rounded-lg p-4 text-center">
              <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">{product.popularity_stats.daily_searches}</p>
              <p className="text-slate-500 dark:text-slate-400">Поисков/день</p>
            </div>
          </div>
        </section>
      )}

      {/* Прогноз цены */}
      {product.price_prediction && (
        <section>
          <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 mb-4">📈 Прогноз цены</h2>
          <div className="bg-slate-50 dark:bg-slate-900 rounded-lg p-6 space-y-4">
            {/* График истории цен */}
            {product.price_history.length > 0 && (
              <div className="mb-4">
                <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">История цен</h3>
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart
                    data={product.price_history
                      .slice(-20)
                      .map((p) => ({
                        date: new Date(p.date).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' }),
                        price: p.price,
                      }))}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis dataKey="date" tick={{ fontSize: 10 }} stroke="#64748b" />
                    <YAxis tick={{ fontSize: 11 }} stroke="#64748b" tickFormatter={(v) => `${(v/1000).toFixed(0)}k`} />
                    <Tooltip
                      formatter={(value) => (typeof value === 'number' ? `${value.toLocaleString('ru-RU')} ₽` : String(value ?? ''))}
                      contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', color: '#e2e8f0' }}
                    />
                    <Line type="monotone" dataKey="price" stroke="#3b82f6" strokeWidth={2} dot={false} name="Цена" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}

            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <p className="text-sm text-slate-500 dark:text-slate-400">Сейчас</p>
                <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                  {product.price_prediction.current_price.toLocaleString('ru-RU', { maximumFractionDigits: 0 })} ₽
                </p>
              </div>
              <div>
                <p className="text-sm text-slate-500 dark:text-slate-400">Через 1 мес</p>
                <p className={`text-2xl font-bold ${
                  (product.price_prediction.predicted_1m || 0) > product.price_prediction.current_price
                    ? 'text-red-600 dark:text-red-400'
                    : 'text-green-600 dark:text-green-400'
                }`}>
                  {product.price_prediction.predicted_1m?.toLocaleString('ru-RU', { maximumFractionDigits: 0 }) ?? '—'} ₽
                </p>
              </div>
              <div>
                <p className="text-sm text-slate-500 dark:text-slate-400">Через 3 мес</p>
                <p className={`text-2xl font-bold ${
                  (product.price_prediction.predicted_3m || 0) > product.price_prediction.current_price
                    ? 'text-red-600 dark:text-red-400'
                    : 'text-green-600 dark:text-green-400'
                }`}>
                  {product.price_prediction.predicted_3m?.toLocaleString('ru-RU', { maximumFractionDigits: 0 }) ?? '—'} ₽
                </p>
              </div>
            </div>

            {/* Рекомендация */}
            <div className={`text-center p-3 rounded-lg font-medium ${
              product.price_prediction.recommendation === 'buy_now'
                ? 'bg-red-100 dark:bg-red-900/40 text-red-800 dark:text-red-200'
                : product.price_prediction.recommendation === 'wait'
                  ? 'bg-yellow-100 dark:bg-yellow-900/40 text-yellow-800 dark:text-yellow-200'
                  : 'bg-blue-100 dark:bg-blue-900/40 text-blue-800 dark:text-blue-200'
            }`}>
              {product.price_prediction.recommendation === 'buy_now' && '🔴 Покупать сейчас — цена растёт'}
              {product.price_prediction.recommendation === 'wait' && '🟡 Подождать — цена снижается'}
              {product.price_prediction.recommendation === 'no_rush' && '⚪ Можно не спешить — цена стабильна'}
              {product.price_prediction.confidence && (
                <span className="ml-2 text-xs opacity-75">(уверенность: {(product.price_prediction.confidence * 100).toFixed(0)}%)</span>
              )}
            </div>

            {/* Тренд */}
            <div className="text-center text-sm text-slate-500 dark:text-slate-400">
              Тренд: {product.price_prediction.trend === 'rising' ? '📈 Растёт' : product.price_prediction.trend === 'falling' ? '📉 Падает' : '➡️ Стабилен'}
            </div>
          </div>
        </section>
      )}

      {/* Аналоги */}
      <section>
        <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 mb-4">Рекомендуемые аналоги</h2>
        <AlternativesList alternatives={alternatives} sourceProductId={id ? Number(id) : undefined} />
      </section>
    </div>
  );
}
