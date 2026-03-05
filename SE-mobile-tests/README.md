# SE Mobile Tests

Автотесты mobile web для Sport-Express на Python + Pytest + Playwright + Allure.

## Что изменено
- Убрана динамическая генерация тестов через `globals()`.
- Запуск идет через нормальную параметризацию: `URL x target`.
- Добавлен target `real_iphone` для Safari на физическом iPhone через Appium.

## Targets
- `iphone13` — эмуляция Playwright `iPhone 13`
- `pixel7` — эмуляция Playwright `Pixel 7`
- `real_iphone` — реальный iPhone (Safari + Appium)

По умолчанию:
- `--targets iphone13,pixel7`

## Установка
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# .\venv\Scripts\Activate.ps1  # Windows

pip install -r requirements.txt
python -m playwright install
```

## Базовый запуск
```bash
pytest --alluredir=allure-results
```

## Явный запуск только эмуляторов
```bash
pytest --targets iphone13,pixel7 --alluredir=allure-results
```

## Запуск на физическом iPhone (macOS)

### 1. Подготовка
```bash
pip install -r requirements-ios.txt
npm i -g appium
appium driver install xcuitest
```

Проверь:
- iPhone подключен кабелем и доверяет Mac.
- На iPhone включен Developer Mode.
- Xcode установлен.

### 2. Узнать параметры устройства
```bash
xcrun xctrace list devices
```

Нужны:
- `IOS_UDID`
- `IOS_DEVICE_NAME`
- `IOS_PLATFORM_VERSION`
- `IOS_XCODE_ORG_ID` (Apple Team ID)

### 3. Запустить Appium
```bash
appium --address 127.0.0.1 --port 4723
```

### 4. Запустить тесты
```bash
export IOS_UDID="<udid>"
export IOS_DEVICE_NAME="<device name>"
export IOS_PLATFORM_VERSION="<ios version>"
export IOS_XCODE_ORG_ID="<apple_team_id>"
export IOS_XCODE_SIGNING_ID="Apple Development"
export IOS_WDA_BUNDLE_ID="ru.<unique>.WebDriverAgentRunner"

pytest -n 1 \
  --targets real_iphone \
  --appium-url http://127.0.0.1:4723 \
  --alluredir=allure-results
```

Важно:
- Для `real_iphone` обязателен `-n 1`.
- Проверка console errors для Safari/Appium недоступна (в отчете есть отдельная пометка).
- При ошибке `xcodebuild failed with code 70` нужно настроить подпись WDA:
  - открыть `Xcode -> Settings -> Accounts` и добавить Apple ID;
  - проверить Team ID;
  - использовать `IOS_XCODE_ORG_ID`, `IOS_XCODE_SIGNING_ID`, `IOS_WDA_BUNDLE_ID`.

## Переменные окружения
- `BASE_URL` — подмена домена для всех URL из `config/urls_mobile.txt`.
- `HEADLESS=1` — headless режим Playwright.
- `ALLOW_INSECURE=1` — разрешить insecure контент для нестандартных окружений.
- `APPIUM_URL` — URL Appium (по умолчанию `http://127.0.0.1:4723`).
- `IOS_UDID`, `IOS_DEVICE_NAME`, `IOS_PLATFORM_VERSION` — параметры реального iPhone.
- `IOS_XCODE_ORG_ID`, `IOS_XCODE_SIGNING_ID`, `IOS_WDA_BUNDLE_ID` — подпись WebDriverAgent.

## Статусы
- Для `/asdasdasd/` ожидается `404`.
- Для остальных URL допустимы: `200`, `301`, `302`, `304`.

## Allure
```bash
allure serve allure-results
```
