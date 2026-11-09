import random, hashlib
from collections import Counter
from pymongo import MongoClient
from datetime import datetime, timedelta

# --- ПОДКЛЮЧЕНИЕ К MONGODB ---
try:
    client = MongoClient("mongodb://localhost:27017/")
    db = client["gik_shop"]
    col_inventory = db["inventory"]
    col_sales = db["sales"]
    print("✅ Успешное подключение к MongoDB!")
except Exception as e:
    print(f"❌ Ошибка подключения к MongoDB. Убедитесь, что сервер запущен. Ошибка: {e}")
    exit()

# --- НАСТРОЙКИ ---
SHARDS = 3
categories = {
    0: "Гаджеты",
    1: "Игры и консоли",
    2: "Комиксы и манга",
    3: "Аниме-атрибутика",
    4: "Коллекционные фигурки"
}

names = ["Алексей", "Мария", "Иван", "Елена", "Дмитрий", "Анна", "Сергей", "Ольга", "Максим", "Ксения", "Гик",
         "Станислав"]

# Корзина
cart = []
cart_total = 0


def stable_hash(value):
    digest = hashlib.sha256(str(value).encode()).digest()
    return int.from_bytes(digest[:8], 'big')


def low_card_category(row):
    return row['category'] % SHARDS


def hashed_customer(row):
    return stable_hash(row['customerId']) % SHARDS


# --- ФУНКЦИИ РАБОТЫ С БАЗОЙ ---
def init_inventory():
    old_item = col_inventory.find_one({"price": {"$exists": False}})
    if old_item:
        print("⚠️ Обнаружены старые товары без цен. Очищаем склад для обновления...")
        col_inventory.delete_many({})

    if col_inventory.count_documents({}) == 0:
        print("📦 База пуста. Добавляем стартовые товары с ценами в тенге...")
        start_items = [
            {"cat_id": 0, "name": "Механическая клавиатура", "qty": 15, "price": 18500,
             "desc": "RGB-подсветка, свитчи Red."},
            {"cat_id": 0, "name": "Игровая мышь", "qty": 25, "price": 9500, "desc": "8000 DPI, беспроводная."},
            {"cat_id": 0, "name": "VR-шлем", "qty": 4, "price": 145000, "desc": "Oculus Quest 2, 128 ГБ."},
            {"cat_id": 1, "name": "PlayStation 5", "qty": 3, "price": 280000, "desc": "Дисковод, 1 геймпад."},
            {"cat_id": 1, "name": "Игра Cyberpunk 2077", "qty": 10, "price": 22000, "desc": "Диск для PS5."},
            {"cat_id": 1, "name": "Геймпад Xbox", "qty": 12, "price": 35000, "desc": "Беспроводной, Carbon Black."},
            {"cat_id": 2, "name": "Манга 'Наруто' том 1", "qty": 30, "price": 2800, "desc": "Мягкая обложка, 192 стр."},
            {"cat_id": 2, "name": "Комикс 'Marvel'", "qty": 15, "price": 4500, "desc": "Твердый переплет."},
            {"cat_id": 3, "name": "Футболка с ИТ-мемом", "qty": 40, "price": 6500, "desc": "Хлопок 100%."},
            {"cat_id": 3, "name": "Кружка 'Hello World'", "qty": 50, "price": 2500, "desc": "Керамика."},
            {"cat_id": 4, "name": "Фигурка Геральта", "qty": 3, "price": 25000, "desc": "Высота 25 см."},
            {"cat_id": 4, "name": "Статуэтка Пикачу", "qty": 8, "price": 18000, "desc": "Светится в темноте."}
        ]
        col_inventory.insert_many(start_items)


def show_stats():
    total_sales = col_sales.count_documents({})
    if total_sales == 0:
        print("\n⚠️ Журнал продаж пуст.")
        return

    print("\n--- СТАТИСТИКА РАСПРЕДЕЛЕНИЯ ПРОДАЖ ---")
    print(f"Всего записей о продажах в MongoDB: {total_sales}")

    all_sales = list(col_sales.find())
    for name, fn in [('category (Низкая кардинальность)', low_card_category),
                     ('hashed_customerId (Высокая)', hashed_customer)]:
        docs = Counter(fn(r) for r in all_sales)
        d = [docs[i] for i in range(SHARDS)]
        doc_max_mean = round(max(d) / (sum(d) / SHARDS), 2) if sum(d) > 0 else 0
        print(f"Ключ {name}: Документы по шардам {d}, Max/mean = {doc_max_mean}")
    print("----------------------------------------\n")


def show_inventory():
    print("\n--- ТЕКУЩИЙ СКЛАД ---")
    items = list(col_inventory.find())
    if not items:
        print("Склад пуст.")
    for item in items:
        status = "✅" if item['qty'] > 0 else "❌ НЕТ В НАЛИЧИИ"
        price = item.get('price', 0)
        print(f"[{item['cat_id']}] {item['name']} — {price} тенге ({item['qty']} шт.) {status}")
        print(f"      Описание: {item.get('desc', 'Без описания')}")
    print("----------------------\n")


def show_cart():
    global cart, cart_total
    print("\n--- ВАША КОРЗИНА ---")
    if not cart:
        print("Корзина пуста.")
        return

    cart_total = 0
    for i, item in enumerate(cart):
        item_total = item['price'] * item['qty']
        cart_total += item_total
        print(f"{i + 1}. {item['name']} | {item['qty']} шт. x {item['price']} тенге = {item_total} тенге")
    print("-" * 30)
    print(f"ИТОГО ЗА ТОВАРЫ: {cart_total} тенге\n")


def show_order_history():
    print("\n--- ИСТОРИЯ ЗАКАЗОВ ---")
    orders = list(col_sales.find({"address": {"$exists": True}}).sort("order_date", -1))

    if not orders:
        print("Пока нет оформленных заказов.")
        return

    for order in orders:
        print(f"📦 Заказ от: {order.get('order_date', 'Неизвестно')}")
        print(f"   Клиент:   {order.get('customerName', 'Неизвестно')}")
        print(f"   Состав:   {order.get('items_summary', 'Неизвестно')}")
        print(
            f"   Сумма:    {order.get('total_items_price', 0)} тенге (товары) + {order.get('delivery_price', 0)} тенге (доставка)")
        print(f"   Итого:    {order.get('grand_total', 0)} тенге")
        print(f"   Адрес:    {order.get('address', '-')}")
        print(f"   Доставка: {order.get('delivery_type', '-')}")
        print(f"   Доставим: {order.get('expected_delivery_date', 'Неизвестно')}")
        print("-" * 50)
    print(f"Всего оформленных заказов: {len(orders)}\n")


# --- ГЛАВНЫЙ ЦИКЛ ---
init_inventory()
print("\nДобро пожаловать в ГИК-МАГАЗИН!")

while True:
    print("\n1. Сгенерировать 12000 случайных продаж")
    print("2. Добавить товар в корзину")
    print("3. Посмотреть корзину")
    print("4. Оформить заказ (из корзины)")
    print("5. Показать склад")
    print("6. Добавить товар на склад")
    print("7. История заказов")
    print("8. Показать статистику шардирования")
    print("9. Выйти")

    choice = input("Ваш выбор (1-9): ")

    if choice == '1':
        print("Генерация 12000 записей...")
        sales_batch = []
        for i in range(12000):
            cat = random.randint(0, 4)
            prod_doc = col_inventory.find_one({"cat_id": cat})
            prod_name = prod_doc["name"] if prod_doc else "Товар"
            sales_batch.append({
                "customerId": i % 2500, "customerName": random.choice(names),
                "category": cat, "product": prod_name, "event_id": i
            })
        col_sales.insert_many(sales_batch)
        print(f"Готово! Добавлено {len(sales_batch)} записей.")

    elif choice == '2':
        try:
            print("\n--- ДОБАВЛЕНИЕ В КОРЗИНУ ---")
            print("\nДоступные категории:")
            for k, v in categories.items():
                print(f"  {k} - {v}")
            cat_id = int(input("Введите категорию (0-4): "))

            items_in_cat = list(col_inventory.find({"cat_id": cat_id}))
            if items_in_cat:
                print(f"\nТовары в категории '{categories[cat_id]}':")
                for i, item in enumerate(items_in_cat):
                    price = item.get('price', 0)
                    print(f"  {i} - {item['name']} | {price} тенге | В наличии: {item['qty']} шт.")

                prod_idx = int(input("Выберите номер товара: "))

                if 0 <= prod_idx < len(items_in_cat):
                    chosen_item = items_in_cat[prod_idx]
                    item_price = chosen_item.get('price', 0)
                    available_qty = chosen_item['qty']

                    if available_qty > 0:
                        buy_qty = int(input(f"Сколько штук добавить? (В наличии: {available_qty}): "))

                        if buy_qty <= 0:
                            print("❌ Ошибка: количество должно быть больше нуля.")
                            continue

                        # --- НОВОЕ: ПРОВЕРКА, ХВАТАЕТ ЛИ ТОВАРА ---
                        if buy_qty > available_qty:
                            print(
                                f"\n⚠️ Внимание! Вы хотите купить {buy_qty} шт., но на складе осталось только {available_qty} шт.")
                            confirm = input(f"Взять все оставшиеся {available_qty} шт.? (да/нет): ").lower()

                            if confirm == 'да':
                                buy_qty = available_qty
                                print(f"✅ Добавлено максимально возможное количество: {buy_qty} шт.")
                            else:
                                print("❌ Отменено. Возврат в меню.")
                                continue

                        # Добавляем в корзину
                        existing_in_cart = False
                        for c_item in cart:
                            if c_item['_id'] == chosen_item['_id']:
                                c_item['qty'] += buy_qty
                                existing_in_cart = True
                                break

                        if not existing_in_cart:
                            cart.append({
                                "_id": chosen_item["_id"],
                                "name": chosen_item["name"],
                                "price": item_price,
                                "qty": buy_qty,
                                "category": cat_id
                            })
                        print(f"✅ Товар '{chosen_item['name']}' ({buy_qty} шт.) добавлен в корзину!")
                    else:
                        print("❌ Товара нет в наличии!")
        except ValueError:
            print("❌ Ошибка: нужно вводить числа.")

    elif choice == '3':
        show_cart()

    elif choice == '4':
        if not cart:
            print("\n⚠️ Корзина пуста. Сначала добавьте товары (пункт 2).")
            continue

        show_cart()
        confirm = input("Подтвердить оформление заказа? (да/нет): ").lower()
        if confirm != 'да':
            continue

        try:
            print("\n--- ОФОРМЛЕНИЕ ЗАКАЗА ---")
            cust_name = input("Введите имя клиента: ")
            cust_id = int(input("Введите ID клиента (число): "))

            print("\n--- ДОСТАВКА ---")
            address = input("Введите адрес доставки (город, улица, дом): ")
            print("Выберите способ доставки:")
            print("  1. Курьер (600 тенге, доставка сегодня через 2 часа)")
            print("  2. Пункт выдачи (300 тенге, будет готов завтра)")
            print("  3. Самовывоз (0 тенге, можно забрать через 15 минут)")
            delivery_choice = input("Ваш выбор (1-3): ")

            delivery_type = "Самовывоз"
            delivery_price = 0

            now = datetime.now()
            if delivery_choice == '1':
                delivery_type, delivery_price = "Курьер", 600
                expected_date = now + timedelta(hours=2)
            elif delivery_choice == '2':
                delivery_type, delivery_price = "ПВЗ", 300
                expected_date = now + timedelta(days=1)
            else:
                expected_date = now + timedelta(minutes=15)

            order_time = now.strftime("%Y-%m-%d %H:%M")
            expected_delivery_date = expected_date.strftime("%Y-%m-%d %H:%M")

            # Уменьшаем склад
            for cart_item in cart:
                col_inventory.update_one({"_id": cart_item["_id"]}, {"$inc": {"qty": -cart_item["qty"]}})

            items_summary = ", ".join([f"{item['name']} ({item['qty']} шт.)" for item in cart])
            grand_total = cart_total + delivery_price

            last_sale = col_sales.find_one(sort=[("event_id", -1)])
            new_event_id = (last_sale["event_id"] + 1) if last_sale else 0

            col_sales.insert_one({
                "customerId": cust_id,
                "customerName": cust_name,
                "items_summary": items_summary,
                "total_items_price": cart_total,
                "grand_total": grand_total,
                "address": address,
                "delivery_type": delivery_type,
                "delivery_price": delivery_price,
                "order_date": order_time,
                "expected_delivery_date": expected_delivery_date,
                "event_id": new_event_id
            })

            print("\n" + "=" * 45)
            print("🧾 ЧЕК ОБ ОПЛАТЕ")
            print("=" * 45)
            print(f"Клиент: {cust_name} (ID: {cust_id})")
            print(f"Состав заказа:")
            for item in cart:
                print(f"  - {item['name']} x {item['qty']} шт. = {item['price'] * item['qty']} тенге")
            print(f"Доставка: {delivery_type} ({delivery_price} тенге)")
            print(f"Адрес:  {address}")
            print(f"Время заказа: {order_time}")
            print(f"Ожидаемое время доставки: {expected_delivery_date}")
            print(f"ИТОГО К ОПЛАТЕ: {grand_total} тенге")
            print("=" * 45)

            cart.clear()

        except ValueError:
            print("❌ Ошибка: нужно вводить числа там, где это требуется.")

    elif choice == '5':
        show_inventory()

    elif choice == '6':
        try:
            cat_id = int(input("Введите категорию (0-4): "))
            if cat_id not in categories:
                print("❌ Неверная категория.")
                continue
            new_prod = input("Название товара: ").strip()
            new_desc = input("Описание товара: ").strip()
            price = int(input("Цена товара (в тенге): "))
            qty = int(input("Количество: "))

            existing = col_inventory.find_one({"cat_id": cat_id, "name": new_prod})
            if existing:
                col_inventory.update_one({"_id": existing["_id"]},
                                         {"$inc": {"qty": qty}, "$set": {"price": price, "desc": new_desc}})
                print("✅ Количество и цена обновлены.")
            else:
                col_inventory.insert_one(
                    {"cat_id": cat_id, "name": new_prod, "desc": new_desc, "price": price, "qty": qty})
                print(f"✅ Новый товар '{new_prod}' добавлен в MongoDB.")
        except ValueError:
            print("❌ Ошибка ввода.")

    elif choice == '7':
        show_order_history()

    elif choice == '8':
        show_stats()

    elif choice == '9':
        print("Выход из программы.")
        break
    else:
        print("Неверный ввод.")
