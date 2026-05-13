"""Статические страницы (о проекте, политика конфиденциальности)"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()


PRIVACY_HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Политика конфиденциальности — PC Parts Advisor</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 640px; margin: 40px auto; padding: 0 20px; color: #334155; line-height: 1.6; }
    h1 { color: #0f172a; }
    h2 { color: #1e293b; margin-top: 24px; }
    a { color: #2563eb; }
    .back { margin-top: 32px; padding-top: 16px; border-top: 1px solid #e2e8f0; }
  </style>
</head>
<body>
  <h1>Политика конфиденциальности</h1>
  <p style="color:#64748b;font-size:0.875rem;">Дата вступления в силу: 9 апреля 2026 г.</p>

  <h2>1. Общие положения</h2>
  <p>Настоящая Политика определяет порядок обработки персональных данных пользователей сервиса PC Parts Advisor в соответствии с 152-ФЗ.</p>

  <h2>2. Цели сбора</h2>
  <ul>
    <li>Обработка обращений через форму обратной связи</li>
    <li>Подписка на уведомления (при согласии)</li>
    <li>Улучшение качества Сервиса</li>
  </ul>

  <h2>3. Состав данных</h2>
  <p>Электронная почта, имя, текст обращения — только при явном согласии пользователя.</p>

  <h2>4. Хранение и защита</h2>
  <p>Хэширование паролей (bcrypt), шифрование (AES-256). Данные хранятся не более 12 месяцев.</p>

  <h2>5. Передача третьим лицам</h2>
  <p>Данные не передаются третьим лицам, кроме случаев, предусмотренных законодательством РФ.</p>

  <h2>6. Права пользователя</h2>
  <p>Пользователь может запросить, исправить или удалить свои данные: privacy@example.com</p>

  <div class="back">
    <a href="/">Вернуться на главную</a>
  </div>
</body>
</html>
"""

ABOUT_HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>О проекте — PC Parts Advisor</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 640px; margin: 40px auto; padding: 0 20px; color: #334155; line-height: 1.6; }
    h1 { color: #0f172a; }
    h2 { color: #1e293b; margin-top: 24px; }
    a { color: #2563eb; }
    .tech { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 12px; }
    .card { background: #f8fafc; padding: 12px; border-radius: 8px; }
    .card strong { display: block; color: #0f172a; }
    .back { margin-top: 32px; padding-top: 16px; border-top: 1px solid #e2e8f0; }
  </style>
</head>
<body>
  <h1>О проекте</h1>
  <p style="font-size:1.125rem;">PC Parts Advisor — система рекомендаций по оценке цен на компьютерные комплектующие.</p>

  <h2>Что делает сервис</h2>
  <p>Помогает оценить обоснованность наценки на GPU, CPU, RAM, SSD, HDD, M.2. Вы видите себестоимость, рыночную цену и оценку наценки.</p>

  <h2>Алгоритм</h2>
  <p>Базовая наценка = (рыночная цена - себестоимость) / себестоимость * 100%. Корректируется по факторам: бренд (0.25), качество (0.30), актуальность (0.20), популярность (0.25). Порог: 40%.</p>

  <h2>Технологии</h2>
  <div class="tech">
    <div class="card"><strong>Frontend</strong>React, TypeScript, Tailwind</div>
    <div class="card"><strong>Backend</strong>FastAPI, Python 3.11</div>
    <div class="card"><strong>База данных</strong>PostgreSQL 15</div>
    <div class="card"><strong>Инфраструктура</strong>Redis, Docker</div>
  </div>

  <h2>Контакты</h2>
  <p><a href="mailto:support@example.com">support@example.com</a></p>

  <div class="back">
    <a href="/">Вернуться на главную</a>
  </div>
</body>
</html>
"""


@router.get("/privacy", response_class=HTMLResponse)
async def privacy_page():
    """Страница политики конфиденциальности"""
    return PRIVACY_HTML


@router.get("/about", response_class=HTMLResponse)
async def about_page():
    """Страница о проекте"""
    return ABOUT_HTML
