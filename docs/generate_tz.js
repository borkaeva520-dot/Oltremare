const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  AlignmentType, HeadingLevel, BorderStyle, WidthType, ShadingType,
  LevelFormat, PageBreak, Header, Footer, PageNumber
} = require('docx');
const fs = require('fs');

const DARK = "1A1A2E";
const GOLD = "C9A96E";
const LIGHT_BG = "F5F0E8";
const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: border, bottom: border, left: border, right: border };

function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 400, after: 200 },
    children: [new TextRun({ text, bold: true, size: 32, color: DARK, font: "Arial" })]
  });
}
function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 280, after: 140 },
    children: [new TextRun({ text, bold: true, size: 26, color: "2E4057", font: "Arial" })]
  });
}
function p(text, opts = {}) {
  return new Paragraph({
    spacing: { before: 80, after: 80 },
    alignment: opts.center ? AlignmentType.CENTER : AlignmentType.JUSTIFIED,
    children: [new TextRun({ text, size: 22, font: "Arial", bold: opts.bold || false })]
  });
}
function bullet(text) {
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    spacing: { before: 60, after: 60 },
    children: [new TextRun({ text, size: 22, font: "Arial" })]
  });
}
function numbered(text) {
  return new Paragraph({
    numbering: { reference: "numbers", level: 0 },
    spacing: { before: 60, after: 60 },
    children: [new TextRun({ text, size: 22, font: "Arial" })]
  });
}
function empty() { return new Paragraph({ children: [new TextRun("")] }); }
function pageBreak() {
  return new Paragraph({ children: [new PageBreak()] });
}

function makeTable(headers, rows, colWidths) {
  const totalWidth = colWidths.reduce((a, b) => a + b, 0);
  return new Table({
    width: { size: totalWidth, type: WidthType.DXA },
    columnWidths: colWidths,
    rows: [
      new TableRow({
        tableHeader: true,
        children: headers.map((h, i) => new TableCell({
          borders,
          width: { size: colWidths[i], type: WidthType.DXA },
          shading: { fill: "1A1A2E", type: ShadingType.CLEAR },
          margins: { top: 80, bottom: 80, left: 120, right: 120 },
          children: [new Paragraph({ children: [new TextRun({ text: h, bold: true, size: 20, color: "FFFFFF", font: "Arial" })] })]
        }))
      }),
      ...rows.map((row, ri) => new TableRow({
        children: row.map((cell, i) => new TableCell({
          borders,
          width: { size: colWidths[i], type: WidthType.DXA },
          shading: { fill: ri % 2 === 0 ? "FFFFFF" : "F5F0E8", type: ShadingType.CLEAR },
          margins: { top: 80, bottom: 80, left: 120, right: 120 },
          children: [new Paragraph({ children: [new TextRun({ text: cell, size: 20, font: "Arial" })] })]
        }))
      }))
    ]
  });
}

const doc = new Document({
  numbering: {
    config: [
      { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "numbers", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    ]
  },
  styles: {
    default: { document: { run: { font: "Arial", size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: "Arial", color: DARK },
        paragraph: { spacing: { before: 400, after: 200 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: "Arial", color: "2E4057" },
        paragraph: { spacing: { before: 280, after: 140 }, outlineLevel: 1 } },
    ]
  },
  sections: [{
    properties: {
      page: { size: { width: 11906, height: 16838 }, margin: { top: 1440, right: 1134, bottom: 1440, left: 1701 } }
    },
    headers: {
      default: new Header({
        children: [new Paragraph({
          border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: GOLD, space: 1 } },
          children: [new TextRun({ text: "Техническое задание — Система управления рестораном «Oltremare»", size: 18, color: "888888", font: "Arial" })]
        })]
      })
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.RIGHT,
          border: { top: { style: BorderStyle.SINGLE, size: 4, color: GOLD, space: 1 } },
          children: [
            new TextRun({ text: "Страница ", size: 18, color: "888888", font: "Arial" }),
            new TextRun({ children: [PageNumber.CURRENT], size: 18, color: "888888", font: "Arial" }),
          ]
        })]
      })
    },
    children: [
      // Титульная страница
      empty(), empty(), empty(),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 0, after: 120 },
        children: [new TextRun({ text: "МИНИСТЕРСТВО ОБРАЗОВАНИЯ", size: 22, font: "Arial" })] }),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 0, after: 40 },
        children: [new TextRun({ text: "Государственное профессиональное образовательное учреждение", size: 22, font: "Arial" })] }),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 0, after: 400 },
        children: [new TextRun({ text: "Специальность 09.02.07 «Информационные системы и программирование»", size: 22, font: "Arial" })] }),

      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 0, after: 40 },
        border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: GOLD, space: 4 } },
        children: [new TextRun({ text: "ТЕХНИЧЕСКОЕ ЗАДАНИЕ", bold: true, size: 40, font: "Arial", color: DARK })] }),
      empty(),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 0, after: 60 },
        children: [new TextRun({ text: "на разработку автоматизированной информационной системы", size: 24, font: "Arial", color: "444444" })] }),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 0, after: 40 },
        children: [new TextRun({ text: "управления рестораном", size: 24, font: "Arial", color: "444444" })] }),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 0, after: 400 },
        children: [new TextRun({ text: "«OLTREMARE»", bold: true, size: 36, font: "Arial", color: GOLD })] }),

      empty(), empty(),
      new Paragraph({ alignment: AlignmentType.RIGHT, spacing: { before: 0, after: 60 },
        children: [new TextRun({ text: "Дисциплина: УП 02.01", size: 22, font: "Arial" })] }),
      new Paragraph({ alignment: AlignmentType.RIGHT, spacing: { before: 0, after: 60 },
        children: [new TextRun({ text: "Студент: [ ФИО студента ]", size: 22, font: "Arial" })] }),
      new Paragraph({ alignment: AlignmentType.RIGHT, spacing: { before: 0, after: 60 },
        children: [new TextRun({ text: "Группа: [ номер группы ]", size: 22, font: "Arial" })] }),
      new Paragraph({ alignment: AlignmentType.RIGHT, spacing: { before: 0, after: 60 },
        children: [new TextRun({ text: "Руководитель: [ ФИО руководителя ]", size: 22, font: "Arial" })] }),
      empty(), empty(),
      new Paragraph({ alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: "2026 г.", size: 22, font: "Arial" })] }),

      pageBreak(),

      // 1. Общие сведения
      h1("1. Общие сведения"),
      h2("1.1 Наименование системы"),
      p("Автоматизированная информационная система управления рестораном «Oltremare» (далее — «Система» или «Приложение»)."),

      h2("1.2 Основание для разработки"),
      p("Основанием для разработки является задание по учебной практике УП 02.01 по специальности 09.02.07 «Информационные системы и программирование»."),

      h2("1.3 Назначение системы"),
      p("Система предназначена для автоматизации процессов управления рестораном: бронирования столиков, приёма и обработки заказов, управления сменами официантов, формирования чеков и статистической отчётности."),

      h2("1.4 Сведения о ресторане"),
      p("Ресторан «Oltremare» — двухэтажный ресторан классической итальянской кухни. Режим работы: ежедневно с 9:00 до 23:00. Вместимость: несколько залов со столиками на 1–4 посетителей каждый."),

      pageBreak(),

      // 2. Требования к системе
      h1("2. Требования к системе"),
      h2("2.1 Роли пользователей"),
      p("В системе предусмотрены следующие роли:"),
      bullet("Администратор — полный доступ ко всем функциям системы"),
      bullet("Официант — управление заказами, работа со своими столиками, открытие/закрытие смены"),
      bullet("Кухня — просмотр и изменение статусов заказов"),
      bullet("Клиент — бронирование столиков (через интерфейс приложения)"),
      empty(),

      h2("2.2 Функциональные требования"),
      h2("2.2.1 Управление бронированием"),
      bullet("Создание брони на конкретную дату и время с указанием количества гостей"),
      bullet("Выбор одного или нескольких столиков при бронировании"),
      bullet("Контроль количества мест: не более 4 за столиком"),
      bullet("Отмена существующей брони"),
      bullet("Изменение даты, времени и стола/столов в брони"),
      bullet("Просмотр схемы расположения столиков и их доступности"),
      empty(),

      h2("2.2.2 Управление заказами"),
      bullet("Создание заказа официантом для конкретного столика"),
      bullet("Добавление блюд в заказ с проверкой наличия на складе кухни"),
      bullet("Удаление блюд из заказа (только при статусе «Составление»)"),
      bullet("Статусы заказа: Составление → Оформлен → Принят в готовку → Готовится → Готов к выдаче → Выдан клиенту / Отменён"),
      bullet("Уменьшение остатка на складе при добавлении блюда в заказ"),
      bullet("Уведомления при добавлении/удалении блюд"),
      empty(),

      h2("2.2.3 Управление счётами и оплатой"),
      bullet("Формирование счёта по заказам клиента"),
      bullet("Применение скидок на блюда или категории блюд (акции)"),
      bullet("Оплата счёта и формирование чека"),
      bullet("Печать/сохранение чека"),
      empty(),

      h2("2.2.4 Управление сменами"),
      bullet("Открытие смены официантом"),
      bullet("Закрытие смены официантом"),
      bullet("Формирование графика смен администратором"),
      bullet("Прикрепление официантов к столикам в рамках смены"),
      empty(),

      h2("2.2.5 Статистика и отчётность"),
      bullet("Список продаж блюд за два месяца с группировкой по категориям"),
      bullet("Динамика продаж (разница между месяцами)"),
      bullet("Количество броней по столикам за выбранный месяц"),
      bullet("Работа официантов за два месяца (заказы, чеки, суммы, динамика)"),
      bullet("Список свободных столиков на дату и время"),
      bullet("Сводная таблица занятости столиков по часам на выбранную дату"),
      empty(),

      h2("2.2.6 Администрирование"),
      bullet("Управление меню (категории, блюда, цены, наличие)"),
      bullet("Управление пользователями и ролями"),
      bullet("Управление столиками"),
      bullet("Управление акциями и скидками"),
      bullet("Просмотр всех броней и заказов"),
      empty(),

      pageBreak(),

      h2("2.3 Нефункциональные требования"),
      makeTable(
        ["Характеристика", "Требование"],
        [
          ["Язык разработки", "Python 3.11+"],
          ["GUI-фреймворк", "Tkinter (стандартная библиотека Python)"],
          ["СУБД", "MySQL 8.0+ / MariaDB 10.6+"],
          ["ORM / доступ к БД", "mysql-connector-python или SQLAlchemy"],
          ["ОС разработки", "macOS (VS Code)"],
          ["Целевые ОС", "Windows 10+, macOS 12+, Linux"],
          ["Время отклика UI", "Не более 2 секунд для стандартных операций"],
          ["Безопасность", "Хранение паролей в виде хеша (bcrypt/hashlib)"],
          ["VCS", "Git с ветвлением (feature-branches → main)"],
          ["Кодирование", "UTF-8, стандарт PEP 8"],
        ],
        [5500, 3800]
      ),
      empty(),

      pageBreak(),

      // 3. Модели данных
      h1("3. Модели данных (описание сущностей)"),
      p("Ниже перечислены основные сущности базы данных:"),
      empty(),

      makeTable(
        ["Сущность", "Назначение", "Ключевые поля"],
        [
          ["Users", "Пользователи системы", "id, login, password_hash, role, full_name, phone"],
          ["Tables", "Столики ресторана", "id, number, capacity, floor, status"],
          ["Shifts", "Смены работы", "id, waiter_id, date, start_time, end_time, status"],
          ["ShiftTables", "Столики в смене", "id, shift_id, table_id"],
          ["Reservations", "Брони столиков", "id, client_name, phone, date, time_start, time_end, guests_count, status"],
          ["ReservationTables", "Столики в брони", "id, reservation_id, table_id"],
          ["MenuCategories", "Категории меню", "id, name, sort_order"],
          ["MenuItems", "Блюда меню", "id, category_id, name, price, description, stock_qty"],
          ["Promotions", "Акции/скидки", "id, name, discount_pct, date_start, date_end, is_active"],
          ["PromotionItems", "Блюда в акции", "id, promotion_id, menu_item_id"],
          ["Orders", "Заказы", "id, reservation_id, table_id, waiter_id, status, created_at, total_amount"],
          ["OrderItems", "Блюда в заказе", "id, order_id, menu_item_id, quantity, price_at_order, discount_pct"],
          ["Bills", "Счета", "id, reservation_id, total_amount, discount_amount, status, created_at"],
          ["Receipts", "Чеки", "id, bill_id, paid_amount, paid_at, waiter_id"],
        ],
        [2800, 3200, 3300]
      ),
      empty(),

      pageBreak(),

      // 4. Интерфейс
      h1("4. Требования к интерфейсу"),
      h2("4.1 Общий стиль"),
      p("Интерфейс выполнен в стиле ресторана Oltremare: тёмный фон (#1A1A2E), золотые акценты (#C9A96E), светлые кремовые элементы (#F5F0E8). Шрифт — Georgia / Helvetica."),

      h2("4.2 Экраны приложения"),
      bullet("Экран входа / регистрации"),
      bullet("Главное меню (зависит от роли)"),
      bullet("Схема расположения столиков (интерактивная)"),
      bullet("Управление бронированием"),
      bullet("Управление заказами и меню"),
      bullet("Кухня: очередь заказов и изменение статусов"),
      bullet("Управление сменами"),
      bullet("Статистика и отчёты"),
      bullet("Администрирование (пользователи, меню, акции)"),
      empty(),

      pageBreak(),

      // 5. Этапы реализации
      h1("5. Этапы реализации"),
      makeTable(
        ["№", "Этап", "Результат"],
        [
          ["1", "Анализ предметной области", "Описание бизнес-процессов, выявление сущностей"],
          ["2", "Разработка ТЗ", "Настоящий документ"],
          ["3", "Проектирование БД", "ER-диаграмма, физическая модель, SQL-скрипт"],
          ["4", "Проектирование UML", "Диаграммы вариантов использования"],
          ["5", "Разработка модулей", "Модули: db, models, ui, utils"],
          ["6", "Интеграция модулей", "Git-ветвление, слияние в main"],
          ["7", "Тестирование", "Модульные, интеграционные, системные тесты"],
          ["8", "Проверка стандартов", "PEP 8, pylint/flake8"],
          ["9", "Документация", "Инструкция пользователя (.docx + README.md)"],
          ["10", "Защита", "Презентация и отчёт"],
        ],
        [600, 4000, 4700]
      ),
      empty(),

      pageBreak(),

      // 6. Тестирование
      h1("6. Требования к тестированию"),
      h2("6.1 Виды тестирования"),
      bullet("Модульное тестирование — тестирование отдельных функций (unittest / pytest)"),
      bullet("Интеграционное тестирование — проверка взаимодействия модулей и БД"),
      bullet("Системное тестирование — сценарии использования от лица каждой роли"),
      empty(),
      h2("6.2 Покрытие"),
      p("Обязательному тестированию подлежат: логика заказов (проверка склада, статусы), логика броней (конфликты дат), расчёт счёта и скидок, аутентификация."),

      pageBreak(),

      // 7. Приложения
      h1("7. Приложения"),
      p("Приложение А — UML-диаграмма вариантов использования (см. файл uml_use_case.png)"),
      p("Приложение Б — ER-диаграмма базы данных (см. файл er_diagram.png)"),
      p("Приложение В — Блок-схема основного алгоритма (см. файл flowchart.png)"),
      p("Приложение Г — SQL-скрипт создания базы данных (см. файл database.sql)"),
      empty(),
    ]
  }]
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync('/home/claude/oltremare/docs/ТЗ_Oltremare.docx', buf);
  console.log('TZ done');
});
