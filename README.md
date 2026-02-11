# SEm — Mobile Web Autotests (Sport-Express)

Автотесты для мобильной версии Sport-Express (m.sport-express.ru) на **Python + Pytest + Playwright** с отчётами **Allure**.  
Тесты гоняются в эмуляции устройств **iPhone 13** и **Pixel 7**.

---

## 1) Требования

### Windows
- **Python 3.11+** (проверка: `python --version`)
- **Git** (проверка: `git --version`)
- **Node.js** (нужен для Allure CLI) — проверка: `node --version`

### Allure CLI
Отчёт открывается командой `allure serve allure-results`.

Проверка:
```powershell
allure --version
Если allure не найден — установи Allure CLI (см. раздел “Установка Allure CLI”).

2) Клонирование репозитория
powershell
Копировать код
cd C:\Users\<USER>\Documents
git clone https://github.com/Fidail333/SEm.git
cd .\SEm\SE-mobile-tests
3) Первый запуск (установка зависимостей)
Все команды ниже выполняй в папке SE-mobile-tests.

3.1 Создать виртуальное окружение
powershell
Копировать код
python -m venv venv
3.2 Активировать виртуальное окружение
powershell
Копировать код
.\venv\Scripts\Activate.ps1
Должно появиться (venv) в начале строки.

3.3 Установить зависимости
powershell
Копировать код
python -m pip install -U pip
python -m pip install -r requirements.txt
3.4 Установить браузеры Playwright
powershell
Копировать код
python -m playwright install
4) Запуск тестов
4.1 Запуск через скрипт (рекомендуется)
powershell
Копировать код
.\scripts\run.ps1
Скрипт:

проверяет/активирует venv

запускает pytest с генерацией allure-results

открывает Allure отчёт (если Allure CLI установлен)

4.2 Запуск вручную (если нужно)
Вариант без параллели:

powershell
Копировать код
pytest --alluredir=allure-results
Вариант в 4 потока (быстрее):

powershell
Копировать код
pytest -n 4 --alluredir=allure-results
Открыть отчёт:

powershell
Копировать код
allure serve allure-results
5) Headless / “видимый браузер”
По умолчанию браузер запускается видимым (не headless).

Чтобы включить headless:

powershell
Копировать код
$env:HEADLESS="1"
.\scripts\run.ps1
Чтобы вернуть видимый режим:

powershell
Копировать код
Remove-Item Env:HEADLESS -ErrorAction SilentlyContinue
.\scripts\run.ps1
6) Что проверяют тесты
Smoke-переходы по списку URL мобильной версии https://m.sport-express.ru/...

Проверка доступности страницы (коды 200/301/302/304)

Негативный кейс только один:
https://m.sport-express.ru/asdasdasd/ — ожидается 404

Ошибки консоли браузера не валят тесты (логируются в Allure как предупреждения)

7) Структура Allure отчёта
В Allure отчёте тесты группируются по устройствам:

SE Mobile Web

iPhone 13

Smoke URLs

Pixel 7

Smoke URLs

8) Важные папки
tests/ — тесты

conftest.py — фикстуры Playwright, настройка устройств/контекстов, сбор логов

pytest.ini — настройки pytest (включая параллельность/ретраи/таймауты)

scripts/run.ps1 — запуск тестов + Allure

allure-results/ — результаты (генерируются локально, в Git НЕ коммитятся)

venv/ — локальное окружение (в Git НЕ коммитится)

9) Типичные проблемы и решения
9.1 pytest: error: unrecognized arguments: -n
Значит не установлен pytest-xdist в текущем venv.

Решение:

powershell
Копировать код
.\venv\Scripts\Activate.ps1
python -m pip install -U pytest-xdist
pytest --help | findstr -i "numprocesses"
9.2 allure: command not found / allure не распознан
Нужно установить Allure CLI.

Установка через npm (рекомендуется)
powershell
Копировать код
npm i -g allure-commandline --save-dev
allure --version
Если команда не появилась — перезапусти терминал/IDE.

9.3 Virtual environment not found. Run setup first
Ты запускаешь run.ps1, но ещё не создал venv.

Решение:

powershell
Копировать код
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m playwright install
9.4 scripts\run.ps1 not recognized
Ты находишься не в той папке.

Правильно:

powershell
Копировать код
cd C:\Users\<USER>\Documents\SEm\SE-mobile-tests
dir scripts
.\scripts\run.ps1
9.5 В отчёте Allure пусто / allure-results does not exist
Pytest не создал результаты (часто из-за ошибки запуска).

Решение:

сначала запусти pytest --alluredir=allure-results

убедись, что папка появилась:

powershell
Копировать код
dir allure-results
затем allure serve allure-results

10) Разработка и пуш в GitHub
Пушим только код/конфиги, НЕ пушим venv и allure-results.

Проверка:

powershell
Копировать код
git status
Команды:

powershell
Копировать код
git add .
git commit -m "Update mobile tests"
git push
11) Полезные команды
Очистить результаты Allure:

powershell
Копировать код
Remove-Item -Recurse -Force allure-results -ErrorAction SilentlyContinue
Запуск одного теста:

powershell
Копировать код
pytest -k mobile_smoke --alluredir=allure-results
Контакты / поддержка
Если что-то не стартует:

пришли вывод команды python --version, pytest --version, allure --version

и первые 30 строк лога запуска .\scripts\run.ps1

