import { Link } from 'react-router-dom';

export default function PrivacyPage() {
  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100">Политика конфиденциальности</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-2">Дата вступления в силу: 9 апреля 2026 г.</p>
      </div>

      <section className="space-y-4 text-slate-700 dark:text-slate-300 leading-relaxed">
        <div>
          <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-100">1. Общие положения</h2>
          <p className="mt-2">
            Настоящая Политика конфиденциальности определяет порядок обработки и защиты персональных данных пользователей
            веб-сервиса &laquo;PC Parts Advisor&raquo; (далее — Сервис) в соответствии с Федеральным законом от 27.07.2006
            N 152-ФЗ &laquo;О персональных данных&raquo;.
          </p>
          <p className="mt-2">
            Оператором персональных данных является администрация Сервиса. Обработка данных осуществляется на территории
            Российской Федерации.
          </p>
        </div>

        <div>
          <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-100">2. Цели сбора персональных данных</h2>
          <p className="mt-2">Персональные данные собираются исключительно для следующих целей:</p>
          <ul className="list-disc list-inside mt-2 space-y-1">
            <li>Обработка обращений через форму обратной связи</li>
            <li>Подписка на уведомления об обновлениях цен (при явном согласии)</li>
            <li>Улучшение качества работы Сервиса</li>
            <li>Обеспечение безопасности пользователей</li>
          </ul>
        </div>

        <div>
          <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-100">3. Состав собираемых данных</h2>
          <p className="mt-2">Сервис может обрабатывать следующие данные:</p>
          <ul className="list-disc list-inside mt-2 space-y-1">
            <li>Электронная почта (при подписке или обращении)</li>
            <li>Имя (при заполнении формы обратной связи)</li>
            <li>Текст обращения</li>
          </ul>
          <p className="mt-2 text-sm text-slate-500">
            Сбор данных осуществляется только при явном согласии пользователя (отметка чекбокса).
          </p>
        </div>

        <div>
          <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-100">4. Правовые основания обработки</h2>
          <p className="mt-2">
            Обработка персональных данных осуществляется на основании:
          </p>
          <ul className="list-disc list-inside mt-2 space-y-1">
            <li>Согласия субъекта персональных данных (ст. 6 ч. 1 п. 1 152-ФЗ)</li>
            <li>Необходимости исполнения договора (ст. 6 ч. 1 п. 5 152-ФЗ)</li>
          </ul>
        </div>

        <div>
          <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-100">5. Хранение и защита данных</h2>
          <p className="mt-2">
            Для обеспечения безопасности персональных данных применяются следующие меры:
          </p>
          <ul className="list-disc list-inside mt-2 space-y-1">
            <li>Хэширование паролей (bcrypt)</li>
            <li>Шифрование данных (AES-256)</li>
            <li>Ограничение доступа к базам данных</li>
            <li>Регулярное резервное копирование</li>
          </ul>
          <p className="mt-2">
            Персональные данные хранятся не более 12 месяцев с момента последнего взаимодействия или до удаления по запросу пользователя.
          </p>
        </div>

        <div>
          <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-100">6. Передача третьим лицам</h2>
          <p className="mt-2">
            Персональные данные не передаются третьим лицам, за исключением случаев, предусмотренных законодательством
            Российской Федерации.
          </p>
        </div>

        <div>
          <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-100">7. Права пользователя</h2>
          <p className="mt-2">Пользователь имеет право:</p>
          <ul className="list-disc list-inside mt-2 space-y-1">
            <li>Получить информацию о хранимых персональных данных</li>
            <li>Требовать исправления неточных данных</li>
            <li>Требовать удаления персональных данных</li>
            <li>Отозвать согласие на обработку данных</li>
          </ul>
          <p className="mt-2">
            Для реализации прав направьте запрос на: <a href="mailto:privacy@example.com" className="text-blue-600 dark:text-blue-400 hover:underline">privacy@example.com</a>
          </p>
        </div>

        <div>
          <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-100">8. Файлы cookie</h2>
          <p className="mt-2">
            Сервис использует файлы cookie для обеспечения корректной работы и сохранения предпочтений пользователя.
            Пользователь может отключить cookie в настройках браузера, однако это может повлиять на функциональность.
          </p>
        </div>

        <div>
          <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-100">9. Заключительные положения</h2>
          <p className="mt-2">
            Настоящая Политика действует бессрочно до её замены новой редакцией. Администрация вправе вносить изменения,
            которые публикуются на данной странице.
          </p>
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
