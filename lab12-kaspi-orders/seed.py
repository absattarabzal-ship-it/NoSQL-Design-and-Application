import random
from pymongo import MongoClient

# Фиксируем seed для воспроизводимости
random.seed(42)

client = MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=3000)
db = client.nosql_lab12
coll = db.orders
coll.drop()  # Очищаем старую коллекцию

STATUSES = ["CREATED", "PAID", "DELIVERING", "DELIVERED", "CANCELLED", "RETURNED"]
CITIES = ["Almaty", "Astana", "Shymkent", "Karaganda", "Aktobe"]

# Справочник товаров, которые можно заказать
CATALOG = [
    {"productId": 101, "name": "Смартфон Samsung Galaxy S24", "price": 450000},
    {"productId": 102, "name": "Смартфон iPhone 15", "price": 550000},
    {"productId": 103, "name": "Ноутбук Asus VivoBook", "price": 320000},
    {"productId": 104, "name": "Наушники AirPods Pro", "price": 95000},
    {"productId": 105, "name": "Телевизор LG OLED", "price": 600000},
    {"productId": 106, "name": "Пылесос Dyson", "price": 250000},
    {"productId": 107, "name": "Кофемашина De'Longhi", "price": 180000},
    {"productId": 108, "name": "Умные часы Apple Watch", "price": 180000},
    {"productId": 109, "name": "Планшет iPad Air", "price": 350000},
    {"productId": 110, "name": "Клавиатура Logitech", "price": 45000}
]

rows = []
# Увеличиваем базу до 100 000 заказов, чтобы индекс показал разницу
for i in range(100000):
    # Формируем корзину (от 1 до 5 разных товаров)
    cart = []
    total_sum = 0
    num_items = random.randint(1, 5)

    # Выбираем уникальные товары для этой корзины
    chosen_products = random.sample(CATALOG, num_items)

    for prod in chosen_products:
        qty = random.randint(1, 3)  # Количество от 1 до 3 штук
        item_total = prod["price"] * qty
        total_sum += item_total

        cart.append({
            "productId": prod["productId"],
            "name": prod["name"],
            "price": prod["price"],
            "quantity": qty
        })

    rows.append({
        "orderId": i,
        "customerId": random.randint(1, 5000),  # 5000 клиентов
        "status": random.choice(STATUSES),
        "city": random.choice(CITIES),
        "items": cart,  # Корзина с товарами
        "total": total_sum,  # Итоговая сумма
        "itemsCount": num_items,  # Кол-во позиций
        "createdAt": f"2025-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
    })

coll.insert_many(rows)

print("Документов:", coll.count_documents({}))
print("Версия MongoDB:", client.server_info()["version"])
print("Пример заказа:", coll.find_one({"customerId": 10}, {"_id": 0}))