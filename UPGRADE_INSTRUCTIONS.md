# UPGRADE_INSTRUCTIONS.md

> Это **учебная пошаговая инструкция** по доработке проекта **Pharmacy** (Flask + Flask‑SQLAlchemy + SQLite) до соответствия требованиям из `README.md` и формулировкам ВКР.
>
> Цель: закрыть требования:
> - поиск и фильтрация товаров по **названию, категории, производителю, штрих‑коду**;
> - признак **рецептурности** (ввод/сохранение/отображение);
> - **валидация** и понятные сообщения об ошибках;
> - **тестирование** (pytest) с изолированной БД.

---

## 0. Справка по библиотекам проекта (минимум теории, чтобы понимать шаги)

### 0.1. Flask
**Что это:** веб‑фреймворк на Python.

**Что используем в проекте (конкретно):**
- `@main.route('/path')` — декоратор, который регистрирует URL (маршрут) и привязывает его к функции.
- `request` — объект «входящего запроса» (параметры URL, данные формы и т.д.).
- `render_template('x.html', ...)` — рендерит HTML-шаблон Jinja2 и подставляет переменные.
- `redirect(url_for(...))` — делает HTTP‑редирект (перенаправление) после POST (паттерн Post/Redirect/Get).
- `flash(message, category)` — сохраняет одноразовое сообщение для пользователя (например, “успешно” или “ошибка”).

### 0.2. Flask-SQLAlchemy / SQLAlchemy
**Что это:**
- `SQLAlchemy` — ORM и конструктор SQL-запросов.
- `Flask-SQLAlchemy` — удобная интеграция SQLAlchemy с Flask (даёт `db`, `Model`, `query`).

**Что используем в проекте (конкретно):**
- `db.Model` — базовый класс модели (таблицы).
- `db.Column(...)` — описание колонок.
- `Product.query.filter(...)` — построение SQL-запроса.
- `db.session.add(...)`, `db.session.commit()` — запись в БД.
- `IntegrityError` — исключение при нарушении ограничений БД (например, unique).

### 0.3. pytest
**Что это:** фреймворк для автотестов.

**Что используем в проекте (конкретно):**
- `@pytest.fixture()` — фикстуры (подготовка окружения для тестов).
- утверждения `assert ...`.
- запуск `pytest -q`.

---

## 1. Подготовка окружения и старт проекта (делаем один раз)

### 1.1. Открыть терминал в корне проекта

#### 1.1.1. Открыть PowerShell в папке проекта
**Где:** папка, где лежат `run.py`, `create_db.py`, `requirements.txt`.

#### 1.1.2. Проверить, что вы в нужной папке
**Команда:**(Выполнено)
```powershell
Get-Location
```
**Что делает команда:** печатает текущую папку, из которой будут выполняться все команды.

**Ожидаемо:** путь заканчивается на `...\Pharmacy`.

---

### 1.2. Проверить версии Python и pip

#### 1.2.1. Проверить Python
**Команда:**(Выполнено: Python: 3.9.13)
```powershell
python --version
```
**Что делает команда:** показывает версию Python.

#### 1.2.2. Проверить pip
**Команда:**(Выполнено: pip: 25.3)
```powershell
pip --version
```
**Что делает команда:** показывает версию pip и какой Python использует pip.

**Типичная ошибка:** `python`/`pip` указывают на разные интерпретаторы.
**Проверка/решение:** после активации `.venv` повторить `where python` и убедиться, что используется `.venv`.

---

### 1.3. Создать виртуальное окружение

#### 1.3.1. Создать venv
**Команда:**(Выполнено: venv)
```powershell
python -m venv .venv
```
**Что делает команда (построчно):**
- `python` — запускает интерпретатор.
- `-m venv` — запускает встроенный модуль Python для создания виртуального окружения.
- `.venv` — имя папки с окружением.

**Почему это важно:** зависимости дипломного проекта должны быть изолированы (чтобы не ломать системный Python).

---

### 1.4. Активировать виртуальное окружение

#### 1.4.1. Активировать
**Команда:**(Выполнено: venv\Scripts\activate)
```powershell
.\.venv\Scripts\Activate.ps1
```
**Что делает команда:** добавляет `.venv` в PATH текущего терминала → `python` и `pip` начинают ссылаться на окружение.

#### 1.4.2. Проверить, что активировалось
**Команды:**(Выполнено: Python: 3.9.13)
```powershell
where python
python --version
```
**Ожидаемо:** первая строка `where python` содержит путь вроде `...\Pharmacy\.venv\Scripts\python.exe`.

**Типичная ошибка:** PowerShell запрещает запуск скриптов.
**Признак:** “running scripts is disabled”.
**Решение (однократно):**
```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

---

### 1.5. Установить зависимости

#### 1.5.1. Установка
**Команда:**(Выполнено)
```powershell
pip install -r requirements.txt
```
**Что делает команда:**
- `pip install` — установка пакетов.
- `-r requirements.txt` — взять список пакетов из файла.

**Почему так:** гарантирует одинаковые версии библиотек на всех компьютерах.

#### 1.5.2. Проверка
**Команда:**(Выполнено: Flask: 2.3.3)
```powershell
pip show Flask
```
**Ожидаемо:** показывает установленный Flask.

---

### 1.6. (Опционально) Пересоздать базу данных для «чистого» теста

#### 1.6.1. Удалить файл БД, если он есть
**Команда:**(Выполнено)
```powershell
if (Test-Path .\pharmacy.db) { Remove-Item .\pharmacy.db }
```
**Что делает команда:**
- `Test-Path` — проверяет, существует ли файл.
- `Remove-Item` — удаляет файл.

**Почему это иногда нужно:** если вы уже добавляли данные и хотите «начать заново».

---

### 1.7. Создать БД и тестовые данные

#### 1.7.1. Запустить скрипт
**Команда:**(Выполнено: Статистика базы данных: Категорий: 5 Товаров: 7)
```powershell
python create_db.py
```

**Что делает команда (кратко):**
- создаёт таблицы (`db.create_all()`),
- если категорий 0 → добавляет тестовые категории и товары.

#### 1.7.2. Проверка
- В корне проекта появился `pharmacy.db`.

---

### 1.8. Запустить приложение

#### 1.8.1. Запуск
**Команда:**(Выполнено)
```powershell
python run.py
```

#### 1.8.2. Проверка в браузере
- `http://127.0.0.1:5000/`
- `http://127.0.0.1:5000/products`

---

## 2. Поиск и фильтрация товаров (обязательное требование)

### 2.1. Изменить backend: расширить `GET /products`

#### 2.1.1. Файл и место правки
- Файл: `app/routes.py`
- Функция: `products()`

#### 2.1.2. Как НАЙТИ нужный код (чтобы не редактировать «не то»)
1) Откройте файл `app/routes.py`.
2) Нажмите поиск по файлу (обычно `Ctrl+F`).
3) Введите строку:
   - `def products`  
   или
   - `@main.route('/products')`
4) Убедитесь, что вы видите функцию, которая начинается примерно так:

```text
@main.route('/products')
def products():
    """Список всех товаров"""
    search = request.args.get('search', '')
    ...
```

Это и есть участок, который нужно заменить.

#### 2.1.3. Что делает СТАРЫЙ код (текущий в репозитории)
Старая версия логики (по смыслу):
1) Берёт из URL только `search`.
2) Если `search` не пустой → фильтрует **только по названию** товара (`Product.name.contains(search)`).
3) Если `search` пустой → показывает все товары.
4) Передаёт в шаблон:
   - `products` (список товаров)
   - `categories` (список категорий)
   - `search` (строка поиска)

**Почему этого недостаточно:** по требованиям README нужно фильтровать также по категории, производителю и штрих‑коду.

#### 2.1.4. Что будет делать НОВЫЙ код (после правки)
Новая версия:
1) Берёт из URL 4 параметра:
   - `search` (название)
   - `category_id`
   - `manufacturer`
   - `barcode`
2) Собирает один SQLAlchemy‑запрос и добавляет фильтры только если пользователь их реально ввёл.
3) Возвращает в шаблон не только товары, но и значения фильтров — чтобы форма «помнила», что вы вводили.

#### 2.1.5. Действия по шагам (что именно делаем)
1) Выделите в `app/routes.py` всю функцию `products()` целиком (от строки `@main.route('/products')` до `return render_template(...)`).
2) Удалите этот блок.
3) Вставьте вместо него новый блок кода из шага **2.1.6**.

#### 2.1.6. Код, который нужно вставить (НОВЫЙ)
```text
@main.route('/products')
def products():
    """Список товаров + поиск/фильтры по названию, категории, производителю, штрих-коду."""

    # 1) Параметры фильтрации из URL
    search = request.args.get('search', '').strip()
    category_id_raw = request.args.get('category_id', '').strip()
    manufacturer = request.args.get('manufacturer', '').strip()
    barcode = request.args.get('barcode', '').strip()

    # 2) Собираем запрос постепенно
    query = Product.query

    # 3) Поиск по названию (частичное совпадение)
    if search:
        query = query.filter(Product.name.contains(search))

    # 4) Фильтр по категории (category_id должен быть числом)
    selected_category_id = None
    if category_id_raw:
        try:
            selected_category_id = int(category_id_raw)
            query = query.filter(Product.category_id == selected_category_id)
        except ValueError:
            flash('Некорректная категория в фильтре (category_id должен быть числом).', 'warning')

    # 5) Поиск по производителю (частичное совпадение)
    if manufacturer:
        query = query.filter(Product.manufacturer.contains(manufacturer))

    # 6) Поиск по штрих-коду (обычно точное совпадение)
    if barcode:
        query = query.filter(Product.barcode == barcode)

    # 7) Получаем список товаров из БД
    products_list = query.all()

    # 8) Категории нужны для select в форме фильтров
    categories = Category.query.all()

    # 9) Передаём обратно в шаблон и товары, и введённые фильтры
    return render_template(
        'products.html',
        products=products_list,
        categories=categories,
        search=search,
        category_id=selected_category_id,
        manufacturer=manufacturer,
        barcode=barcode,
    )
```

#### 2.1.7. Проверка работоспособности (ДО/ПОСЛЕ) — как проверять правильно

##### 2.1.7.1. Проверка ДО правки (для понимания разницы)
1) Откройте в браузере:
   - `http://127.0.0.1:5000/products?search=Нурофен`
2) Ожидаемо:
   - в таблице видите позиции, где **название** содержит «Нурофен».
3) Что происходит в коде (кратко):
   - Flask читает `search` через `request.args.get('search')`.
   - SQLAlchemy делает фильтр `Product.name.contains(search)`.

4) Откройте:
   - `http://127.0.0.1:5000/products?manufacturer=Bayer`
5) Ожидаемо ДО правки:
   - список, скорее всего, **не меняется**, потому что старый код не читает `manufacturer`.

##### 2.1.7.2. Проверка ПОСЛЕ правки (основные сценарии)

**Сценарий A: фильтр по названию**
1) Откройте:
   - `http://127.0.0.1:5000/products?search=Нурофен`
2) Ожидаемо:
   - список сократился до товаров, где `name` содержит «Нурофен».
3) Что происходит в коде:
   - `search` считывается из URL.
   - выполняется `query.filter(Product.name.contains(search))`.

**Сценарий B: фильтр по производителю**
1) Откройте:
   - `http://127.0.0.1:5000/products?manufacturer=Bayer`
2) Ожидаемо:
   - остались товары, у которых `manufacturer` содержит «Bayer».
3) Что происходит в коде:
   - `manufacturer` читается из URL.
   - выполняется `query.filter(Product.manufacturer.contains(manufacturer))`.

**Сценарий C: фильтр по штрих‑коду**
1) Откройте:
   - `http://127.0.0.1:5000/products?barcode=123456789012`
2) Ожидаемо:
   - найден либо один товар, либо ничего (если штрих‑кода нет).
3) Что происходит в коде:
   - `barcode` читается из URL.
   - выполняется `query.filter(Product.barcode == barcode)` (точное совпадение).

**Сценарий D: фильтр по категории**
1) Откройте:
   - `http://127.0.0.1:5000/products?category_id=1`
2) Ожидаемо:
   - остались товары, у которых `category_id == 1`.
3) Что происходит в коде:
   - `category_id_raw` читается строкой.
   - `int(category_id_raw)` превращает строку в число.
   - выполняется `query.filter(Product.category_id == selected_category_id)`.

##### 2.1.7.3. Проверка граничного случая (плохие данные)
1) Откройте:
   - `http://127.0.0.1:5000/products?category_id=abc`
2) Ожидаемо:
   - страница **не падает** (нет белого экрана/500).
   - список товаров показывается (скорее всего без фильтра по категории).
   - (если у вас в шаблоне выводятся flash‑сообщения) показывается предупреждение.
3) Что происходит в коде:
   - `int('abc')` вызывает `ValueError`.
   - мы ловим его в `except ValueError`.
   - вызываем `flash(...)` и продолжаем работу без фильтра категории.

##### 2.1.7.4. Как понять, что именно сломалось (если не работает)
- Если при открытии `/products?...` вы видите “Internal Server Error 500”, то:
  1) проверьте консоль сервера (терминал, где запущен `python run.py`) — там будет трассировка.
  2) чаще всего проблема в том, что:
     - вы не передали в `render_template` какую-то переменную (`manufacturer`, `barcode`, `category_id`),
     - или в шаблоне `products.html` используете переменную, которой нет.

---

#### 2.2. Изменить frontend: добавить форму фильтров на `products.html`

#### 2.2.1. Файл и место правки
- Файл: `app/templates/products.html`

#### 2.2.2. Как НАЙТИ нужный код
1) Откройте файл `app/templates/products.html`.
2) Нажмите `Ctrl+F`.
3) Ищите одно из:
   - `name="search"`
   - `<form`
   - слово `Поиск` (если в шаблоне есть кнопка)

Ваша цель — найти форму, которая отправляет `search`.

#### 2.2.3. Что делает СТАРАЯ форма
- Обычно она содержит одно поле `search`.
- Старая форма не умеет отправлять `category_id`, `manufacturer`, `barcode`.

#### 2.2.4. Что будет делать НОВАЯ форма
- Отправляет параметры в URL (GET):
  - `search`, `category_id`, `manufacturer`, `barcode`
- Сохраняет введённые значения в полях через `value="{{ ... }}"`.

#### 2.2.5. Что вставить
> Вставляйте/заменяйте форму целиком в том месте, где у вас сейчас форма поиска.

```jinja2
<form method="get" action="{{ url_for('main.products') }}" class="mb-3">
  <div>
    <label>Название:</label>
    <input type="text" name="search" value="{{ search or '' }}" placeholder="Например: Нурофен">
  </div>

  <div>
    <label>Категория:</label>
    <select name="category_id">
      <option value="">Все категории</option>
      {% for c in categories %}
        <option value="{{ c.id }}" {% if category_id == c.id %}selected{% endif %}>{{ c.name }}</option>
      {% endfor %}
    </select>
  </div>

  <div>
    <label>Производитель:</label>
    <input type="text" name="manufacturer" value="{{ manufacturer or '' }}" placeholder="Например: Bayer">
  </div>

  <div>
    <label>Штрих-код:</label>
    <input type="text" name="barcode" value="{{ barcode or '' }}" placeholder="Например: 123456789012">
  </div>

  <button type="submit">Поиск / Фильтр</button>
  <a href="{{ url_for('main.products') }}">Сбросить</a>
</form>
```

#### 2.2.6. Проверка работоспособности (после изменения формы)

##### 2.2.6.1. Проверка, что форма отправляет параметры
1) Откройте страницу:
   - `http://127.0.0.1:5000/products`
2) Введите в поле "Производитель" значение, например `Bayer`.
3) Нажмите кнопку "Поиск / Фильтр".
4) Ожидаемо:
   - адрес в браузере изменится и будет содержать `?manufacturer=Bayer`.

**Что происходит в коде (кратко):**
- Браузер отправляет GET-запрос на `/products` с querystring.
- Flask в `products()` читает `request.args` и применяет фильтр.

##### 2.2.6.2. Проверка, что форма «помнит» введённые значения
1) После фильтрации посмотрите на поле "Производитель".
2) Ожидаемо:
   - в поле всё ещё написано `Bayer`.

**Что происходит в коде:**
- `products()` передаёт `manufacturer=...` в `render_template`.
- Jinja подставляет `value="{{ manufacturer or '' }}"`.

##### 2.2.6.3. Проверка «Сбросить»
1) Нажмите ссылку "Сбросить".
2) Ожидаемо:
   - URL снова без `?....`.
   - показываются все товары.

---

## 3. Признак рецептурности (обязательное требование)

### 3.1. Добавить поле в форму добавления товара

#### 3.1.1. Как НАЙТИ нужный код
1) Откройте `app/templates/add_product.html`.
2) Найдите `<form`.
3) Найдите блоки с полями `name`, `price`, `quantity`.
4) Вставьте чекбокс рядом с ними.

#### 3.1.2. Что делает СТАРАЯ форма
- Отправляет на сервер `name`, `price`, `quantity`, `category_id`, `manufacturer`, `barcode`.
- Не отправляет `requires_prescription`.

#### 3.1.3. Что будет делать НОВАЯ форма
- Добавится чекбокс.
- Если чекбокс отмечен — браузер отправит поле `requires_prescription`.

#### 3.1.4. Код чекбокса (вставить внутрь `<form>`)
```html
<div>
  <label>
    <input type="checkbox" name="requires_prescription">
    Рецептурный препарат
  </label>
</div>
```

#### 3.1.5. Проверка (как именно проверить чекбокс)
1) Откройте:
   - `http://127.0.0.1:5000/add_product`
2) Ожидаемо:
   - на странице есть чекбокс "Рецептурный препарат".

**Что происходит (кратко):**
- Это чисто фронтенд-изменение: вы добавили `<input type="checkbox" ...>` в HTML.

### 3.2. Сохранять `requires_prescription` в `POST /add_product`

#### 3.2.1. Файл и место
- Файл: `app/routes.py`
- Функция: `add_product()`
- Внутри `if request.method == 'POST':`

#### 3.2.2. Код (добавить чтение чекбокса)
```text
requires_prescription = request.form.get('requires_prescription') is not None
```

#### 3.2.3. Код (добавить в создание `Product(...)`)
```text
requires_prescription=requires_prescription,
```

#### 3.2.4. Проверка (как именно проверить сохранение рецептурности)

##### 3.2.4.1. Подготовка
1) Откройте `/add_product`.
2) Заполните обязательные поля (название, цена, количество, категория).

##### 3.2.4.2. Проверка значения True
1) Поставьте галочку "Рецептурный препарат".
2) Нажмите кнопку добавления (submit).
3) Ожидаемо:
   - вы попадёте на страницу `/products`.
   - новый товар появился в списке.

**Что происходит в коде:**
- Flask читает form‑данные через `request.form.get(...)`.
- Для чекбокса:
  - если отмечен → `request.form.get('requires_prescription')` возвращает что-то (обычно `'on'`)
  - мы превращаем это в `True` через `is not None`
- SQLAlchemy сохраняет `requires_prescription=True` в БД.

##### 3.2.4.3. Проверка значения False
1) Добавьте второй товар, но галочку НЕ ставьте.
2) Ожидаемо:
   - второй товар добавился.

**Что происходит в коде:**
- Чекбокс не отправляется → `request.form.get(...)` вернёт `None`.
- Выражение `is not None` даст `False`.

---

### 3.3. Показать рецептурность в списке товаров

#### 3.3.1. Файл
- `app/templates/products.html`

#### 3.3.2. Код
Добавьте в таблицу колонку:
```html
<th>Рецепт</th>
```
И в строку товара:
```html
<td>{% if product.requires_prescription %}Да{% else %}Нет{% endif %}</td>
```

#### 3.3.3. Проверка (как проверить отображение «Да/Нет»)
1) Откройте:
   - `http://127.0.0.1:5000/products`
2) Найдите ваши два тестовых товара.
3) Ожидаемо:
   - у товара с галочкой — "Да"
   - у товара без галочки — "Нет"

**Что происходит в коде:**
- Шаблон выводит `product.requires_prescription`.
- Jinja делает ветвление `{% if ... %}` и печатает "Да" или "Нет".

---

## 4. Валидация и обработка ошибок

### 4.1. Валидация чисел в `add_product`

#### 4.1.1. Файл
- `app/routes.py` → `add_product()`

#### 4.1.2. Код (заменить опасные `float(...)`/`int(...)` на безопасный блок)
> Вставлять **внутри** `if request.method == 'POST':`

```text
try:
    price = float(request.form.get('price'))
    quantity = int(request.form.get('quantity'))
    category_id = int(request.form.get('category_id'))
except (TypeError, ValueError):
    flash('Проверьте поля: цена должна быть числом, количество и категория — целыми числами.', 'danger')
    return redirect(url_for('main.add_product'))

if price < 0:
    flash('Цена не может быть отрицательной.', 'danger')
    return redirect(url_for('main.add_product'))

if quantity < 0:
    flash('Количество не может быть отрицательным.', 'danger')
    return redirect(url_for('main.add_product'))
```

#### 4.1.3. Проверка (валидация чисел — сценарии)

**Сценарий A: ошибка в цене**
1) Откройте `/add_product`.
2) Введите цену: `abc`.
3) Нажмите submit.
4) Ожидаемо:
   - сервер НЕ упадёт.
   - вы вернётесь на форму.
   - увидите сообщение об ошибке (если шаблон выводит flash).

**Что происходит в коде:**
- `float('abc')` выбрасывает `ValueError`.
- `except` ловит исключение.
- `flash(...)` сохраняет сообщение.
- `redirect(...)` возвращает браузер на форму.

**Сценарий B: отрицательные значения**
1) Введите цену `-10`.
2) submit.
3) Ожидаемо:
   - сообщение "Цена не может быть отрицательной".

---

### 4.2. Обработка дубликатов категории (`IntegrityError`)

#### 4.2.1. Файл
- `app/routes.py` → `add_category()`

#### 4.2.2. Код (импорт)
В начало файла добавьте:
```text
from sqlalchemy.exc import IntegrityError
```

#### 4.2.3. Код (try/except вокруг commit)
```text
db.session.add(new_category)
try:
    db.session.commit()
except IntegrityError:
    db.session.rollback()
    flash('Категория с таким именем уже существует. Выберите другое имя.', 'danger')
    return redirect(url_for('main.add_category'))
```

#### 4.2.4. Проверка (дубликат категории)
1) Откройте `http://127.0.0.1:5000/add_category`.
2) Добавьте категорию с именем, которого нет.
3) Добавьте категорию с тем же именем ещё раз.
4) Ожидаемо:
   - приложение не падает.
   - вторую категорию не добавляет.
   - показывает сообщение о том, что имя занято.

**Что происходит в коде:**
- SQLite запрещает вставку (unique constraint).
- SQLAlchemy выбрасывает `IntegrityError` на `commit()`.
- Мы ловим `IntegrityError`, делаем `db.session.rollback()` и показываем `flash`.

---

## 5. Тестирование (pytest) с изолированной БД

### 5.1. Добавить pytest в зависимости

#### 5.1.1. Файл(Выполнено)
- `requirements.txt`

#### 5.1.2. Код(Выполнено)
Добавить строку:
```text
pytest
```

#### 5.1.3. Команда установки(Выполнено)
```powershell
pip install -r requirements.txt
```

#### 5.1.3. Проверка установки pytest(Выполнено Pytest: 8.4.2)(Выполнено)
1) После `pip install -r requirements.txt` выполните:

```powershell
pytest --version
```

2) Ожидаемо:
- печатается версия pytest.

**Что происходит:**
- pip установил пакет `pytest`, теперь команда `pytest` доступна в вашей `.venv`.

### 5.2. Создать фикстуры и тесты

#### 5.2.1. Создать файл `tests/conftest.py`(Выполнено)
```text
import pytest

from app import create_app, db


@pytest.fixture()
def app():
    app = create_app()
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI='sqlite:///test_pharmacy.db',
    )

    with app.app_context():
        db.drop_all()
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()
```

#### 5.2.2. Создать файл `tests/test_pages.py`(Выполнено)
```text
from app.models import Category, Product
from app import db


def test_home_page_returns_200(client):
    resp = client.get('/')
    assert resp.status_code == 200


def test_products_filters_work(client, app):
    with app.app_context():
        cat1 = Category(name='Категория 1')
        cat2 = Category(name='Категория 2')
        db.session.add_all([cat1, cat2])
        db.session.flush()

        p1 = Product(name='Нурофен', price=100.0, quantity=10, category_id=cat1.id, manufacturer='Reckitt', barcode='111', requires_prescription=False)
        p2 = Product(name='Амоксициллин', price=200.0, quantity=5, category_id=cat2.id, manufacturer='Sandoz', barcode='222', requires_prescription=True)
        db.session.add_all([p1, p2])
        db.session.commit()

    resp = client.get('/products?manufacturer=Reckitt')
    assert resp.status_code == 200
    assert 'Нурофен' in resp.get_data(as_text=True)

    resp = client.get('/products?barcode=222')
    assert resp.status_code == 200
    assert 'Амоксициллин' in resp.get_data(as_text=True)
```

#### 5.2.3. Запуск тестов(Выполнено)
```powershell
pytest -q
```

##### 5.2.3.1. Запуск(Выполнено)
```powershell
pytest -q
```

##### 5.2.3.2. Ожидаемый результат
- Вы увидите, что тесты прошли, примерно:
  - `2 passed`

##### 5.2.3.3. Что происходит во время теста (кратко)
- pytest находит `tests/test_*.py`.
- Берёт фикстуру `app()` из `conftest.py`:
  - создаёт Flask‑приложение,
  - подменяет `SQLALCHEMY_DATABASE_URI` на тестовую,
  - создаёт таблицы.
- `client` делает запросы `client.get('/...')` как браузер.

##### 5.2.3.4. Если тесты упали
- Если ошибка про импорт `create_app` → проблема в путях/структуре приложения.
- Если ошибка 500 на `/products` → смотрите трассировку: часто не передали переменную в шаблон.

---

## 6. Финальная проверка перед сдачей

### 6.1. Ручная проверка через браузер
1) `/` — открывается.
2) `/products` — фильтры работают.
3) `/add_product` — можно добавить рецептурный товар.
4) `/categories` — дубликат категории не ломает приложение.

### 6.2. Проверка тестами
```powershell
pytest -q
```
