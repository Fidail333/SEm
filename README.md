# SEm

Репозиторий автотестов mobile web для Sport-Express.

Основной проект:
- [SE-mobile-tests/README.md](SE-mobile-tests/README.md)

Ключевые возможности:
- Playwright smoke на `iphone13` и `pixel7`.
- Опциональный запуск на физическом iPhone (`real_iphone`) через Appium.
- Allure отчеты.

Быстрый старт:
```bash
cd SE-mobile-tests
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m playwright install
pytest --alluredir=allure-results
```
