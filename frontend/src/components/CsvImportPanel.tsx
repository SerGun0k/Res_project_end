import { useState, useRef } from 'react';
import api from '../api/client';

export default function CsvImportPanel() {
  const [file, setFile] = useState<File | null>(null);
  const [source, setSource] = useState('DNS');
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleImport = async () => {
    if (!file) return;

    setLoading(true);
    setResult(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await api.post(`/import-prices-csv?source=${source}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setResult(response.data);
    } catch (err: any) {
      setResult({ error: err.response?.data?.detail || 'Ошибка загрузки' });
    } finally {
      setLoading(false);
    }
  };

  const downloadTemplate = () => {
    const csv = `brand,model,source,price,date,url
NVIDIA,RTX 4070,DNS,62999,2026-04-10,https://www.dns-shop.ru/search/?q=RTX+4070
AMD,Ryzen 7 7800X3D,DNS,34999,2026-04-10,https://www.dns-shop.ru/search/?q=Ryzen+7`;
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'prices_template.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="bg-slate-50 dark:bg-slate-900 rounded-lg p-6 border border-slate-200 dark:border-slate-700">
      <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100 mb-4">📥 Импорт цен из CSV</h3>

      {/* Шаблон */}
      <div className="mb-4">
        <button
          onClick={downloadTemplate}
          className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
        >
          📄 Скачать шаблон CSV
        </button>
      </div>

      {/* Форма */}
      <div className="space-y-3">
        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
            Источник
          </label>
          <select
            value={source}
            onChange={(e) => setSource(e.target.value)}
            className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 text-sm"
          >
            <option value="DNS">DNS</option>
            <option value="Ozon">Ozon</option>
            <option value="Citilink">Citilink</option>
            <option value="Yandex Market">Яндекс.Маркет</option>
            <option value="Manual">Ручной ввод</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
            CSV файл
          </label>
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="w-full text-sm text-slate-600 dark:text-slate-400
              file:mr-4 file:py-2 file:px-4
              file:rounded file:border-0
              file:text-sm file:font-semibold
              file:bg-blue-50 file:text-blue-700
              dark:file:bg-blue-900 dark:file:text-blue-300
              hover:file:bg-blue-100 dark:hover:file:bg-blue-800"
          />
        </div>

        <button
          onClick={handleImport}
          disabled={!file || loading}
          className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition text-sm font-medium"
        >
          {loading ? 'Загрузка...' : 'Импортировать цены'}
        </button>
      </div>

      {/* Результат */}
      {result && (
        <div className={`mt-4 p-4 rounded-lg text-sm ${
          result.error
            ? 'bg-red-50 dark:bg-red-900/30 text-red-800 dark:text-red-200'
            : 'bg-green-50 dark:bg-green-900/30 text-green-800 dark:text-green-200'
        }`}>
          {result.error ? (
            <p>❌ {result.error}</p>
          ) : (
            <div>
              <p className="font-medium">✅ {result.message}</p>
              {result.stats && (
                <div className="mt-2 grid grid-cols-2 gap-2 text-xs">
                  <div>Всего строк: <span className="font-bold">{result.stats.total}</span></div>
                  <div>Импортировано: <span className="font-bold">{result.stats.imported}</span></div>
                  <div>Пропущено: <span className="font-bold">{result.stats.skipped}</span></div>
                  <div>Товар не найден: <span className="font-bold">{result.stats.products_not_found}</span></div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
