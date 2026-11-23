// 1. Переключаемся на нужную базу
db = db.getSiblingDB('support_lab19');

// 2. Создаем данные для тикетов
db.tickets.insertMany([
  {ticketId:2001, subject:"Не входит в личный кабинет", status:"open", priority:"high"},
  {ticketId:2002, subject:"Ошибка при оплате картой", status:"open", priority:"high"},
  {ticketId:2003, subject:"Не приходит SMS-код", status:"pending", priority:"medium"},
  {ticketId:2004, subject:"Как сменить пароль", status:"closed", priority:"low"},
  {ticketId:2005, subject:"Зависает мобильное приложение", status:"open", priority:"medium"}
]);

// 3. Создаем данные для защищенной коллекции
db.internal_notes.insertMany([
  {noteId:3001, ticketId:2001, author:"agent_07", note:"Клиент подтвердил сброс пароля"},
  {noteId:3002, ticketId:2002, author:"agent_12", note:"Требуется проверка шлюза"},
  {noteId:3003, ticketId:2003, author:"agent_03", note:"Проблема на стороне оператора"}
]);

// 4. Создаем данные для журнала аудита
db.audit_events.insertMany([
  {eventId:4001, event:"seed", source:"lab"},
  {eventId:4002, event:"role_created", source:"system"}
]);

// 5. Создаем роли (если они уже есть, скрипт выдаст ошибку, но это не страшно)
try {
  db.createRole({role:"supportViewer", privileges:[{resource:{db:"support_lab19", collection:"tickets"}, actions:["find"]}], roles:[]});
  db.createRole({role:"supportEditor", privileges:[{resource:{db:"support_lab19", collection:"tickets"}, actions:["find","insert","update"]}], roles:[]});
  db.createRole({role:"supportAuditor", privileges:[{resource:{db:"support_lab19", collection:"audit_events"}, actions:["find"]}], roles:[]});
} catch(e) { print("Роли уже существуют"); }

// 6. Создаем пользователей (если они уже есть, скрипт выдаст ошибку, но это не страшно)
try {
  db.createUser({user:"viewer19", pwd:"123", roles:[{role:"supportViewer", db:"support_lab19"}]});
  db.createUser({user:"editor19", pwd:"123", roles:[{role:"supportEditor", db:"support_lab19"}]});
  db.createUser({user:"auditor19", pwd:"123", roles:[{role:"supportAuditor", db:"support_lab19"}]});
} catch(e) { print("Пользователи уже существуют"); }

print("=== СКРИПТ УСПЕШНО ВЫПОЛНЕН ===");