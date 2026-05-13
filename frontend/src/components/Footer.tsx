import { Link } from 'react-router-dom';

export default function Footer() {
  return (
    <footer className="bg-slate-900 dark:bg-slate-950 border-t border-slate-700 dark:border-slate-800 mt-auto text-sm">
      <div className="max-w-7xl mx-auto px-4 py-8 space-y-4">
        <p className="text-center italic text-slate-400 dark:text-slate-500">
          Информация носит оценочный характер. Администрация не несёт ответственности за неактуальность цен и расчётов.
        </p>
        <div className="flex flex-col sm:flex-row justify-between items-center gap-2">
          <div className="flex gap-4">
            <Link to="/about" className="text-slate-400 hover:text-white dark:text-slate-500 dark:hover:text-slate-300 transition">О проекте</Link>
            <Link to="/privacy" className="text-slate-400 hover:text-white dark:text-slate-500 dark:hover:text-slate-300 transition">Политика конфиденциальности</Link>
          </div>
          <p className="text-slate-400 dark:text-slate-500">Контакты: support@example.com</p>
        </div>
        <div className="text-center">
          <p className="text-lg font-bold text-white dark:text-slate-200 tracking-tight">M.A.G.regator</p>
          <p className="text-slate-500 dark:text-slate-600">&copy; 2026 M.A.G.regator. Все права защищены.</p>
        </div>
      </div>
    </footer>
  );
}
