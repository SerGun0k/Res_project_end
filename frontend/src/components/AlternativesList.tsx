import { Link } from 'react-router-dom';
import type { AlternativeProduct } from '../types';
import { getProductImage } from '../utils/images';
import Feedback from './Feedback';

export default function AlternativesList({ alternatives, sourceProductId }: { alternatives: AlternativeProduct[], sourceProductId?: number }) {
  if (alternatives.length === 0) {
    return <p className="text-slate-500 text-sm">Аналоги не найдены</p>;
  }

  return (
    <div className="space-y-3">
      {alternatives.map((alt) => {
        const imgUrl = getProductImage('GPU', alt.brand, alt.model, 120);
        return (
          <div key={alt.product_id} className="border border-slate-200 dark:border-slate-700 rounded-lg p-4 bg-white dark:bg-slate-900">
            <div className="flex gap-4">
              {/* Картинка */}
              <div className="w-20 h-20 bg-slate-50 dark:bg-slate-800 rounded-lg flex items-center justify-center p-2 flex-shrink-0">
                <img
                  src={imgUrl}
                  alt={`${alt.brand} ${alt.model}`}
                  className="max-w-full max-h-full object-contain"
                />
              </div>

              <div className="flex-1">
                <div className="flex justify-between items-start">
                  <div>
                    <Link to={`/product/GPU/${alt.product_id}`} className="font-semibold text-slate-900 dark:text-slate-100 hover:text-blue-600 dark:hover:text-blue-400 transition">
                      {alt.brand} {alt.model}
                    </Link>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Score: {alt.score.toFixed(2)}</p>
                  </div>
                  <span className="text-lg font-bold text-slate-900 dark:text-slate-100">
                    {alt.price.toLocaleString('ru-RU')} ₽
                  </span>
                </div>

                <div className="mt-2 flex flex-wrap gap-3 text-xs text-slate-600 dark:text-slate-400">
                  <span>Наценка: {alt.markup_percent.toFixed(1)}%</span>
                  <span>Качество: {alt.quality_factor.toFixed(2)}</span>
                </div>

                <p className="text-xs text-slate-500 dark:text-slate-400 mt-2 italic">{alt.recommendation}</p>

                {/* Обратная связь */}
                {sourceProductId && (
                  <Feedback productId={sourceProductId} alternativeId={alt.product_id} />
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
