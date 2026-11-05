# Лабораторная №10 — NoSQL. Вариант 3: Интернет-магазин

**Студент:** Док Иска  
**MongoDB:** 9.0.4, Windows  
**Replica Set:** rsLab10 (27101, 27102, 27103)

## Что сделано
- Развёрнут Replica Set из 3 узлов.
- Коллекция shop_lab10.orders — 20 заказов, writeConcern: majority.
- Смоделирован отказ PRIMARY (27103) -> избран новый PRIMARY (27101).
- Узел 27103 возвращён в строй как SECONDARY.
- Сделан mongodump и восстановление в shop_restore10 (20 документов).
