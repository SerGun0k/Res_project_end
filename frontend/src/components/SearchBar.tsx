import { useState, type FormEvent, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

// Словарь подсказок: буква → популярные бренды/модели
const SUGGESTIONS_MAP: Record<string, string[]> = {
  'r': ['RTX 4090', 'RTX 4080', 'RTX 4070', 'RX 7900 XTX', 'RX 7800 XT'],
  'g': ['GTX 1660', 'GT 1030', 'GPU AMD', 'GPU NVIDIA'],
  'i': ['Intel Core i9-14900K', 'Intel Core i7-14700K', 'Intel Core i5-14400', 'Intel Core i3-14100'],
  'a': ['AMD Ryzen 9 7950X', 'AMD Ryzen 7 7800X3D', 'AMD Ryzen 5 7600X', 'AMD Radeon RX 7900'],
  'n': ['NVIDIA RTX 4090', 'NVIDIA RTX 4080', 'NVIDIA RTX 4070 Ti'],
  'c': ['Core i9', 'Core i7', 'Core i5', 'CPU AMD', 'CPU Intel'],
  's': ['Samsung 990 Pro', 'Samsung 870 EVO', 'SSD 1TB', 'SSD 2TB', 'SSD NVMe'],
  'k': ['Kingston Fury', 'Kingston DDR5', 'Kingston DDR4'],
  'd': ['DDR5 32GB', 'DDR5 16GB', 'DDR4 32GB', 'DDR4 16GB'],
  'p': ['PSU 750W', 'PSU 850W', 'PSU 1000W', 'Power Supply'],
  'o': ['Ozon', 'Охлаждение', 'NZXT Kraken'],
};

const CATEGORIES_SUGGESTIONS = ['GPU', 'CPU', 'RAM', 'SSD', 'HDD', 'M2', 'PSU', 'COOLING'];

export default function SearchBar({ initialQuery = '' }: { initialQuery?: string }) {
  const [query, setQuery] = useState(initialQuery);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const navigate = useNavigate();
  const wrapperRef = useRef<HTMLDivElement>(null);

  // Закрытие подсказок при клике вне
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setQuery(value);

    if (value.length === 0) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }

    const firstChar = value[0].toLowerCase();
    const matchedSuggestions = SUGGESTIONS_MAP[firstChar] || [];

    // Фильтруем по введённому тексту
    const filtered = matchedSuggestions.filter((s) =>
      s.toLowerCase().includes(value.toLowerCase())
    );

    // Если есть точное совпадение с категорией
    const catMatch = CATEGORIES_SUGGESTIONS.filter((c) =>
      c.toLowerCase().includes(value.toLowerCase())
    );

    setSuggestions([...catMatch, ...filtered].slice(0, 6));
    setShowSuggestions(true);
  };

  const handleSelect = (suggestion: string) => {
    setQuery(suggestion);
    setShowSuggestions(false);
    navigate(`/search?q=${encodeURIComponent(suggestion)}`);
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    setShowSuggestions(false);
    if (query.trim()) {
      navigate(`/search?q=${encodeURIComponent(query.trim())}`);
    }
  };

  return (
    <div ref={wrapperRef} className="relative w-full max-w-xl">
      <form onSubmit={handleSubmit}>
        <div className="flex">
          <input
            type="text"
            value={query}
            onChange={handleInputChange}
            onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
            placeholder="Поиск комплектующих"
            className="flex-1 px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-l-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500"
          />
          <button
            type="submit"
            className="px-6 py-2 bg-blue-600 text-white rounded-r-lg hover:bg-blue-700 transition font-medium"
          >
            Найти
          </button>
        </div>
      </form>

      {/* Подсказки */}
      {showSuggestions && suggestions.length > 0 && (
        <ul className="absolute z-50 w-full mt-1 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg shadow-lg max-h-60 overflow-auto">
          {suggestions.map((suggestion, idx) => (
            <li
              key={idx}
              onClick={() => handleSelect(suggestion)}
              className="px-4 py-2 hover:bg-blue-50 dark:hover:bg-slate-700 cursor-pointer text-slate-800 dark:text-slate-200 transition"
            >
              {suggestion}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
