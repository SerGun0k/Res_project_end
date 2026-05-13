import { useState, useEffect, useMemo } from 'react';
import type { ProductWithMarkup } from '../types';

interface SearchFiltersProps {
  products: ProductWithMarkup[];
  onFiltered: (filtered: ProductWithMarkup[]) => void;
}

type SortOption = 'price_asc' | 'price_desc' | 'markup_asc' | 'markup_desc' | 'rating_desc' | 'name_asc';

// Карта категорий → бренды
const CATEGORY_BRANDS: Record<string, string[]> = {
  GPU: ['NVIDIA', 'AMD', 'Palit', 'MSI', 'ASUS', 'Gigabyte', 'EVGA', 'Zotac'],
  CPU: ['Intel', 'AMD'],
  RAM: ['Kingston', 'Corsair', 'G.Skill', 'Crucial', 'Patriot', 'ADATA'],
  SSD: ['Samsung', 'Kingston', 'WD', 'Crucial', 'ADATA', 'Seagate', 'Intel'],
  HDD: ['Seagate', 'WD', 'Toshiba', 'Hitachi'],
  PSU: ['Corsair', 'be quiet!', 'Seasonic', 'EVGA', 'Thermaltake', 'Cooler Master'],
  COOLING: ['Noctua', 'be quiet!', 'Corsair', 'NZXT', 'Deepcool', 'Arctic'],
};

export default function SearchFilters({ products, onFiltered }: SearchFiltersProps) {
  const [priceMin, setPriceMin] = useState(0);
  const [priceMax, setPriceMax] = useState(0);
  const [selectedBrands, setSelectedBrands] = useState<string[]>([]);
  const [sort, setSort] = useState<SortOption>('price_asc');
  const [showFilters, setShowFilters] = useState(false);

  // Определяем категорию из продуктов и собираем уникальные бренды
  const category = useMemo(() => {
    const cats = new Set(products.map((p) => p.category));
    return cats.size === 1 ? Array.from(cats)[0] : null;
  }, [products]);

  const brands = useMemo(() => {
    if (category && CATEGORY_BRANDS[category]) {
      return CATEGORY_BRANDS[category];
    }
    return Array.from(new Set(products.map((p) => p.brand).filter(Boolean))).sort();
  }, [category, products]);

  // Вычисляем диапазон цен
  useEffect(() => {
    if (products.length === 0) return;
    const prices = products
      .map((p) => p.market_price)
      .filter((p): p is number => p !== null && p !== undefined && p > 0);

    if (prices.length > 0) {
      const min = Math.floor(Math.min(...prices));
      const max = Math.ceil(Math.max(...prices));
      setPriceMin(min);
      setPriceMax(max);
    } else {
      // Если нет цен — не фильтруем
      setPriceMin(0);
      setPriceMax(Number.MAX_SAFE_INTEGER);
    }
  }, [products]);

  // Фильтрация и сортировка
  useEffect(() => {
    let filtered = [...products];

    // Фильтр по цене (только если есть реальные значения)
    if (priceMin > 0 || (priceMax < Number.MAX_SAFE_INTEGER && priceMax > 0)) {
      filtered = filtered.filter(
        (p) =>
          p.market_price !== null &&
          p.market_price >= priceMin &&
          p.market_price <= priceMax
      );
    }

    // Фильтр по брендам
    if (selectedBrands.length > 0) {
      filtered = filtered.filter((p) => selectedBrands.includes(p.brand));
    }

    // Сортировка
    filtered.sort((a, b) => {
      switch (sort) {
        case 'price_asc':
          return (a.market_price || 0) - (b.market_price || 0);
        case 'price_desc':
          return (b.market_price || 0) - (a.market_price || 0);
        case 'markup_asc':
          return (a.markup_percent || 0) - (b.markup_percent || 0);
        case 'markup_desc':
          return (b.markup_percent || 0) - (a.markup_percent || 0);
        case 'rating_desc': {
          const ra = a.review_quality?.avg_rating || 0;
          const rb = b.review_quality?.avg_rating || 0;
          return rb - ra;
        }
        case 'name_asc':
          return `${a.brand} ${a.model}`.localeCompare(`${b.brand} ${b.model}`, 'ru');
        default:
          return 0;
      }
    });

    onFiltered(filtered);
  }, [products, priceMin, priceMax, selectedBrands, sort, onFiltered]);

  const toggleBrand = (brand: string) => {
    setSelectedBrands((prev) =>
      prev.includes(brand) ? prev.filter((b) => b !== brand) : [...prev, brand]
    );
  };

  const resetFilters = () => {
    setSelectedBrands([]);
    if (products.length > 0) {
      const prices = products
        .map((p) => p.market_price)
        .filter((p): p is number => p !== null && p !== undefined);
      if (prices.length > 0) {
        setPriceMin(Math.floor(Math.min(...prices)));
        setPriceMax(Math.ceil(Math.max(...prices)));
      }
    }
    setSort('price_asc');
  };

  return (
    <div className="space-y-4">
      {/* Кнопка показать/скрыть фильтры */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="text-sm font-medium text-blue-600 dark:text-blue-400 hover:underline"
        >
          {showFilters ? '▲ Скрыть фильтры' : '▼ Показать фильтры'}
        </button>
        {showFilters && (
          <button onClick={resetFilters} className="text-xs text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200">
            Сбросить
          </button>
        )}
      </div>

      {showFilters && (
        <div className="bg-slate-50 dark:bg-slate-900 rounded-lg p-4 space-y-6 border border-slate-200 dark:border-slate-700">
          {/* Ползунок цены */}
          <div>
            <h3 className="font-semibold text-slate-900 dark:text-slate-100 mb-2">Цена, ₽</h3>
            <div className="flex items-center gap-4">
              <div className="flex-1">
                <label className="text-xs text-slate-500 dark:text-slate-400">От</label>
                <input
                  type="number"
                  value={priceMin}
                  onChange={(e) => setPriceMin(Number(e.target.value))}
                  className="w-full px-3 py-1.5 border border-slate-300 dark:border-slate-600 rounded bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 text-sm"
                />
              </div>
              <span className="text-slate-400 mt-5">—</span>
              <div className="flex-1">
                <label className="text-xs text-slate-500 dark:text-slate-400">До</label>
                <input
                  type="number"
                  value={priceMax}
                  onChange={(e) => setPriceMax(Number(e.target.value))}
                  className="w-full px-3 py-1.5 border border-slate-300 dark:border-slate-600 rounded bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 text-sm"
                />
              </div>
            </div>
            {/* Слайдеры */}
            <div className="mt-3 space-y-2">
              <input
                type="range"
                min={priceMin}
                max={priceMax || 1}
                value={priceMin}
                onChange={(e) => setPriceMin(Math.min(Number(e.target.value), priceMax))}
                className="w-full accent-blue-600"
              />
              <input
                type="range"
                min={priceMin || 0}
                max={priceMax || 1}
                value={priceMax}
                onChange={(e) => setPriceMax(Math.max(Number(e.target.value), priceMin))}
                className="w-full accent-blue-600"
              />
            </div>
          </div>

          {/* Чекбоксы брендов */}
          {brands.length > 0 && (
            <div>
              <h3 className="font-semibold text-slate-900 dark:text-slate-100 mb-2">Бренды</h3>
              <div className="flex flex-wrap gap-2">
                {brands.map((brand) => (
                  <label
                    key={brand}
                    className={`flex items-center gap-2 px-3 py-1.5 rounded-full border cursor-pointer text-sm transition ${
                      selectedBrands.includes(brand)
                        ? 'bg-blue-100 dark:bg-blue-900 border-blue-300 dark:border-blue-700 text-blue-800 dark:text-blue-200'
                        : 'bg-white dark:bg-slate-800 border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 hover:border-blue-300'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={selectedBrands.includes(brand)}
                      onChange={() => toggleBrand(brand)}
                      className="sr-only"
                    />
                    <span>{brand}</span>
                  </label>
                ))}
              </div>
            </div>
          )}

          {/* Сортировка */}
          <div>
            <h3 className="font-semibold text-slate-900 dark:text-slate-100 mb-2">Сортировка</h3>
            <select
              value={sort}
              onChange={(e) => setSort(e.target.value as SortOption)}
              className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 text-sm focus:ring-2 focus:ring-blue-500"
            >
              <option value="price_asc">Цена ↑ (дешевле сначала)</option>
              <option value="price_desc">Цена ↓ (дороже сначала)</option>
              <option value="markup_asc">Наценка ↑</option>
              <option value="markup_desc">Наценка ↓</option>
              <option value="rating_desc">Рейтинг ↓</option>
              <option value="name_asc">Название А-Я</option>
            </select>
          </div>
        </div>
      )}
    </div>
  );
}
