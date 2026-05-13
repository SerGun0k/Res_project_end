import { Link } from 'react-router-dom';
import { useTheme } from '../context/ThemeContext';

export default function Header() {
  const { theme, toggleTheme } = useTheme();

  return (
    <header className="bg-gradient-to-r from-slate-800 to-slate-900 dark:from-slate-900 dark:to-black text-white sticky top-0 z-50 shadow-lg border-b border-slate-700/50 dark:border-slate-800">
      <div className="max-w-7xl mx-auto px-4 py-3">
        <div className="flex items-center justify-between">
          <Link to="/" className="text-xl font-bold tracking-tight">
            M.A.G.regator
          </Link>
          <div className="flex items-center gap-4 text-sm text-slate-300">
            <Link to="/" className="hover:text-white transition">Главная</Link>
            <Link to="/search?q=" className="hover:text-white transition">Поиск</Link>
            <Link to="/about" className="hover:text-white transition">О проекте</Link>
            
            {/* Переключатель темы */}
            <button
              onClick={toggleTheme}
              className="ml-2 px-3 py-1 rounded border border-slate-600 hover:bg-slate-800 transition text-xs"
              aria-label={theme === 'dark' ? 'Включить светлую тему' : 'Включить тёмную тему'}
            >
              {theme === 'dark' ? '☀️' : '🌙'}
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
