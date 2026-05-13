import { Link } from 'react-router-dom';
import type { ProductWithMarkup } from '../types';
import { getProductImage } from '../utils/images';

interface ProductCardProps {
  product: ProductWithMarkup;
  onToggleCompare?: (id: number) => void;
  isSelected?: boolean;
}

export default function ProductCard({ product, onToggleCompare, isSelected }: ProductCardProps) {
  const statusColors: Record<string, string> = {
    normal: 'bg-green-100 text-green-800',
    high: 'bg-red-100 text-red-800',
  };

  const statusLabels: Record<string, string> = {
    normal: 'Нормальная',
    high: 'Завышена',
  };

  const imgUrl = getProductImage(
    product.category,
    product.brand,
    product.model,
    200,
    (product.specs as any)?.image_url,
  );
  const url = `/product/${product.category}/${product.id}`;

  return (
    <div
      className={`block border rounded-lg overflow-hidden hover:shadow-md transition group relative ${
        isSelected
          ? 'border-blue-500 dark:border-blue-400 ring-2 ring-blue-200 dark:ring-blue-800'
          : 'border-slate-200 dark:border-slate-700'
      }`}
    >
      {/* Кнопка сравнения */}
      {onToggleCompare && (
        <button
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            onToggleCompare(product.id);
          }}
          className={`absolute top-2 right-2 z-10 w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition ${
            isSelected
              ? 'bg-blue-600 text-white hover:bg-blue-700'
              : 'bg-white/80 dark:bg-slate-800/80 text-slate-600 dark:text-slate-300 hover:bg-blue-100 dark:hover:bg-blue-900 border border-slate-300 dark:border-slate-600'
          }`}
          title="Добавить к сравнению"
        >
          ⚖
        </button>
      )}

      <Link to={url} className="cursor-pointer">
        {/* Картинка */}
        <div className="aspect-[4/3] bg-slate-50 dark:bg-slate-900 flex items-center justify-center p-4">
          <img
            src={imgUrl}
            alt={`${product.brand} ${product.model}`}
            className="max-w-full max-h-full object-contain group-hover:scale-105 transition-transform duration-200"
            onError={(e) => {
              (e.target as HTMLImageElement).style.display = 'none';
            }}
          />
        </div>

        {/* Информация */}
        <div className="p-4">
          <h3 className="font-semibold text-sm text-slate-900 dark:text-slate-100 line-clamp-2">{product.brand} {product.model}</h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            {product.category}{product.subcategory ? ` → ${product.subcategory}` : ''}
          </p>

          <div className="mt-2 flex items-baseline gap-2">
            {product.market_price && (
              <span className="text-base font-bold text-slate-900 dark:text-slate-100">
                {product.market_price.toLocaleString('ru-RU')} ₽
              </span>
            )}
          </div>

          {product.markup_percent != null && (
            <span className={`inline-block text-xs px-2 py-0.5 rounded-full font-medium mt-1 ${statusColors[product.markup_status || ''] || 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400'}`}>
              {statusLabels[product.markup_status || ''] || product.markup_status} ({product.markup_percent}%)
            </span>
          )}

          {product.cost_estimate && (
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-2">
              Себестоимость: {product.cost_estimate.total.toLocaleString('ru-RU')} ₽
            </p>
          )}
        </div>
      </Link>
    </div>
  );
}
