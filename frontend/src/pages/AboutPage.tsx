import { Link } from 'react-router-dom';
import CsvImportPanel from '../components/CsvImportPanel';

export default function AboutPage() {
  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100">О проекте</h1>
        <p className="text-lg text-slate-600 dark:text-slate-400 mt-2">
          M.A.G.regator — система рекомендаций по оценке цен на компьютерные комплектующие.
        </p>
      </div>

      <section className="space-y-4 text-slate-700 dark:text-slate-300 leading-relaxed">
        <div>
          <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-100">Что делает сервис</h2>
          <p className="mt-2">
            Сервис помогает оценить обоснованность наценки на компьютерные комплектующие (GPU, CPU, RAM, SSD, HDD, M.2).
            Вы ищете товар, видите расчётную себестоимость, рыночную цену и оценку наценки с учётом факторов:
          </p>
          <ul className="list-disc list-inside mt-2 space-y-1">
            <li>Премиальность бренда (NVIDIA, AMD, Intel и др.)</li>
            <li>Качество (рейтинг, процент брака)</li>
            <li>Актуальность модели (дата выхода, поддержка)</li>
            <li>Популярность среди пользователей</li>
          </ul>
        </div>

        <div>
          <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-100">Как работает алгоритм</h2>
          <p className="mt-2">
            Для каждого товара рассчитывается базовая наценка относительно расчётной себестоимости,
            которая формируется из стоимости материалов, логистики и затрат на сборку.
            Затем наценка корректируется по взвешенным факторам, и если скорректированное значение
            превышает порог 40%, наценка помечается как завышенная.
          </p>
          <p className="mt-2">
            Сервис также подбирает 3-5 аналогов с лучшим соотношением цена/качество,
            ранжированных по формуле: <code className="bg-slate-100 dark:bg-slate-800 px-1 py-0.5 rounded text-sm">score = (100 / adjusted_markup) x quality x relevance</code>.
          </p>
        </div>

        <div>
          <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-100">Технологии</h2>
          <div className="mt-2 grid grid-cols-2 gap-2 text-sm">
            <div className="bg-slate-50 dark:bg-slate-800 rounded-lg p-3">
              <p className="font-medium text-slate-900 dark:text-slate-100">Frontend</p>
              <p className="text-slate-600 dark:text-slate-400">React 19, TypeScript, Vite, Tailwind CSS</p>
            </div>
            <div className="bg-slate-50 dark:bg-slate-800 rounded-lg p-3">
              <p className="font-medium text-slate-900 dark:text-slate-100">Backend</p>
              <p className="text-slate-600 dark:text-slate-400">FastAPI, Python 3.11, SQLAlchemy</p>
            </div>
            <div className="bg-slate-50 dark:bg-slate-800 rounded-lg p-3">
              <p className="font-medium text-slate-900 dark:text-slate-100">База данных</p>
              <p className="text-slate-600 dark:text-slate-400">PostgreSQL 15, Alembic</p>
            </div>
            <div className="bg-slate-50 dark:bg-slate-800 rounded-lg p-3">
              <p className="font-medium text-slate-900 dark:text-slate-100">Инфраструктура</p>
              <p className="text-slate-600 dark:text-slate-400">Redis 7, Docker, APScheduler</p>
            </div>
          </div>
        </div>

        <div>
          <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-100">Источники данных</h2>
          <p className="mt-2">
            Рыночные цены собираются из открытых источников (API маркетплейсов, прайс-листы).
            Себестоимость рассчитывается на основе отраслевых коэффициентов и усреднённых цен на сырьё.
            Все данные нормализуются к одной валюте (RUB) и дате.
          </p>
        </div>

        <div>
          <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-100">Контакты</h2>
          <p className="mt-2">
            По вопросам работы сервиса: <a href="mailto:support@example.com" className="text-blue-600 dark:text-blue-400 hover:underline">support@example.com</a>
          </p>
        </div>

        <div>
          <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-100">Импорт цен</h2>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-400 mb-4">
            Загрузите реальные цены из CSV файла. Формат: brand, model, price (обязательные поля).
          </p>
          <CsvImportPanel />
        </div>
      </section>

      <div className="pt-4 border-t border-slate-200 dark:border-slate-700">
        <Link to="/" className="text-blue-600 dark:text-blue-400 hover:underline text-sm">
          Вернуться на главную
        </Link>
      </div>
    </div>
  );
}
