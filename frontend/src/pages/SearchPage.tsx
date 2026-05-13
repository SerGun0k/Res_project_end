import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import SearchBar from '../components/SearchBar';
import ProductCard from '../components/ProductCard';
import SearchFilters from '../components/SearchFilters';
import ProductComparison from '../components/ProductComparison';
import { productsApi } from '../api/products';
import type { ProductWithMarkup } from '../types';

export default function SearchPage() {
  const [searchParams] = useSearchParams();
  const query = searchParams.get('q') || '';
  const category = searchParams.get('cat') || '';
  const subcategory = searchParams.get('sub') || '';
  const [results, setResults] = useState<ProductWithMarkup[]>([]);
  const [filteredResults, setFilteredResults] = useState<ProductWithMarkup[]>([]);
  const [selectedForCompare, setSelectedForCompare] = useState<number[]>([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);

  const handleFiltered = useCallback((filtered: ProductWithMarkup[]) => {
    setFilteredResults(filtered);
  }, []);

  const toggleCompare = (productId: number) => {
    setSelectedForCompare((prev) => {
      if (prev.includes(productId)) {
        return prev.filter((id) => id !== productId);
      }
      if (prev.length >= 3) return prev; // максимум 3
      return [...prev, productId];
    });
  };

  const removeCompare = (productId: number) => {
    setSelectedForCompare((prev) => prev.filter((id) => id !== productId));
  };

  const compareProducts = filteredResults.filter((p) => selectedForCompare.includes(p.id));

  useEffect(() => {
    // Если есть категория но нет запроса — ищем все товары категории
    if (category && !query) {
      setLoading(true);
      productsApi.getAll(category, subcategory || undefined, 0, 200)
        .then((res) => {
          // Преобразуем Product[] в ProductWithMarkup[]
          const items: ProductWithMarkup[] = res.data.map((p) => ({
            ...p,
            price_history: [],
            cost_estimate: null,
            review_quality: null,
            popularity_stats: null,
            market_price: null,
            markup_percent: null,
            adjusted_markup: null,
            markup_status: null,
          }));
          setResults(items);
          setTotal(items.length);
        })
        .catch(() => { setResults([]); setTotal(0); })
        .finally(() => setLoading(false));
      return;
    }

    // Если есть запрос — ищем
    if (query) {
      setLoading(true);
      const params: any = { page: 1, per_page: 200 };
      if (category) params.category = category;
      if (subcategory) params.subcategory = subcategory;

      productsApi.search(query, params)
        .then((res) => {
          setResults(res.data.items);
          setTotal(res.data.total);
        })
        .catch(() => {
          setResults([]);
          setTotal(0);
        })
        .finally(() => setLoading(false));
      return;
    }

    // Ничего нет — показываем все
    setResults([]);
    setFilteredResults([]);
    setTotal(0);
  }, [query, category, subcategory]);

  const pageTitle = category
    ? `Категория: ${subcategory ? `${category} → ${subcategory}` : category}`
    : (query ? `Результаты: ${query}` : '');

  return (
    <div className="space-y-8">
      <div className="flex justify-center">
        <SearchBar initialQuery={query} />
      </div>

      {pageTitle && (
        <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100">{pageTitle}</h2>
      )}

      {/* Сравнение товаров */}
      {compareProducts.length >= 2 && (
        <section>
          <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 mb-4">
            Сравнение товаров ({compareProducts.length}/3)
          </h2>
          <ProductComparison products={compareProducts} onRemove={removeCompare} />
        </section>
      )}

      {!query && !category ? (
        <p className="text-center text-slate-500 dark:text-slate-400">Введите запрос для поиска или выберите категорию на главной</p>
      ) : loading ? (
        <p className="text-center text-slate-500 dark:text-slate-400">Поиск...</p>
      ) : results.length === 0 ? (
        <p className="text-center text-slate-500 dark:text-slate-400">Ничего не найдено</p>
      ) : (
        <>
          <div className="flex items-center justify-between">
            <p className="text-sm text-slate-600 dark:text-slate-400">
              Найдено: {filteredResults.length} из {total}
            </p>
            {selectedForCompare.length > 0 && (
              <p className="text-sm text-blue-600 dark:text-blue-400">
                Выбрано для сравнения: {selectedForCompare.length}/3
              </p>
            )}
          </div>

          {/* Фильтры */}
          <SearchFilters products={results} onFiltered={handleFiltered} />

          {/* Результаты */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {filteredResults.map((product) => (
              <ProductCard
                key={product.id}
                product={product}
                onToggleCompare={toggleCompare}
                isSelected={selectedForCompare.includes(product.id)}
              />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
