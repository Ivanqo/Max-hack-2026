from pathlib import Path
from datetime import date

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "documents" / "TZ_presentation_UniPath_MAX.docx"
FONT = "Aptos"
BLACK = RGBColor(0, 0, 0)
BLUE = "1479D1"
DEEP_BLUE = "17365D"
LIGHT_BLUE = "EAF3FA"
LIGHT_GRAY = "F5F7FA"
GRID = "D9D9D9"
GREEN = "E9F6EE"
AMBER = "FFF4D6"


def set_run_font(run, size=None, bold=None, color=None, italic=None):
    run.font.name = FONT
    run._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), FONT)
    run._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), FONT)
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if color is not None:
        run.font.color.rgb = color
    if italic is not None:
        run.italic = italic


def shade(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def cell_margins(cell, top=100, start=130, bottom=100, end=130):
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for m, v in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{m}"))
        if node is None:
            node = OxmlElement(f"w:{m}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(v))
        node.set(qn("w:type"), "dxa")


def borders(cell, color=GRID, size="6"):
    tc_pr = cell._tc.get_or_add_tcPr()
    border = tc_pr.first_child_found_in("w:tcBorders")
    if border is None:
        border = OxmlElement("w:tcBorders")
        tc_pr.append(border)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = border.find(qn(f"w:{edge}"))
        if el is None:
            el = OxmlElement(f"w:{edge}")
            border.append(el)
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), size)
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), color)


def format_table(table, header=True, alternate=True):
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = True
    for ri, row in enumerate(table.rows):
        row.height_rule = None
        for cell in row.cells:
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            cell_margins(cell)
            borders(cell)
            for p in cell.paragraphs:
                p.paragraph_format.space_after = Pt(2)
                p.paragraph_format.line_spacing = 1.03
                for r in p.runs:
                    set_run_font(r, 9.2)
        if header and ri == 0:
            for cell in row.cells:
                shade(cell, DEEP_BLUE)
                for p in cell.paragraphs:
                    for r in p.runs:
                        set_run_font(r, 9.2, bold=True, color=RGBColor(255, 255, 255))
        elif alternate and ri % 2 == 0:
            for cell in row.cells:
                shade(cell, LIGHT_GRAY)


def set_repeat_header(row):
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)


def add_page_number(paragraph):
    run = paragraph.add_run()
    fld_char1 = OxmlElement("w:fldChar")
    fld_char1.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = "PAGE"
    fld_char2 = OxmlElement("w:fldChar")
    fld_char2.set(qn("w:fldCharType"), "end")
    run._r.append(fld_char1)
    run._r.append(instr)
    run._r.append(fld_char2)
    set_run_font(run, 8, color=RGBColor(100, 100, 100))


def add_hyperlink(paragraph, text, url):
    part = paragraph.part
    rid = part.relate_to(url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink", is_external=True)
    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), rid)
    new_run = OxmlElement("w:r")
    r_pr = OxmlElement("w:rPr")
    color = OxmlElement("w:color")
    color.set(qn("w:val"), BLUE)
    r_pr.append(color)
    underline = OxmlElement("w:u")
    underline.set(qn("w:val"), "single")
    r_pr.append(underline)
    fonts = OxmlElement("w:rFonts")
    fonts.set(qn("w:ascii"), FONT)
    fonts.set(qn("w:hAnsi"), FONT)
    r_pr.append(fonts)
    new_run.append(r_pr)
    text_node = OxmlElement("w:t")
    text_node.text = text
    new_run.append(text_node)
    hyperlink.append(new_run)
    paragraph._p.append(hyperlink)
    return hyperlink


def add_para(doc, text="", style=None, bold_prefix=None, color=None, align=None, after=5, size=None):
    p = doc.add_paragraph(style=style)
    if align is not None:
        p.alignment = align
    p.paragraph_format.space_after = Pt(after)
    if bold_prefix and text.startswith(bold_prefix):
        r1 = p.add_run(bold_prefix)
        set_run_font(r1, size=size, bold=True, color=color)
        r2 = p.add_run(text[len(bold_prefix):])
        set_run_font(r2, size=size, color=color)
    else:
        r = p.add_run(text)
        set_run_font(r, size=size, color=color)
    return p


def add_bullets(doc, items, level=0, size=10.2, after=2):
    for item in items:
        p = doc.add_paragraph(style="List Bullet")
        p.paragraph_format.left_indent = Cm(0.55 + level * 0.4)
        p.paragraph_format.first_line_indent = Cm(-0.25)
        p.paragraph_format.space_after = Pt(after)
        r = p.add_run(item)
        set_run_font(r, size=size)


def add_numbered(doc, items, size=10.2, after=3):
    for item in items:
        p = doc.add_paragraph(style="List Number")
        p.paragraph_format.left_indent = Cm(0.55)
        p.paragraph_format.first_line_indent = Cm(-0.25)
        p.paragraph_format.space_after = Pt(after)
        r = p.add_run(item)
        set_run_font(r, size=size)


def add_section_heading(doc, text, level=1):
    p = doc.add_paragraph(style=f"Heading {level}")
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    set_run_font(r, size={1: 16, 2: 13.2, 3: 11.2}.get(level, 11), bold=True, color=BLACK)
    return p


def add_field_table(doc, rows):
    table = doc.add_table(rows=0, cols=2)
    for label, value, tone in rows:
        cells = table.add_row().cells
        cells[0].text = ""
        cells[1].text = ""
        p0 = cells[0].paragraphs[0]
        r0 = p0.add_run(label)
        set_run_font(r0, 9.4, bold=True, color=DEEP_BLUE and BLACK)
        p1 = cells[1].paragraphs[0]
        r1 = p1.add_run(value)
        set_run_font(r1, 9.4)
        if tone:
            shade(cells[1], tone)
    format_table(table, header=False, alternate=False)
    return table


def add_status_table(doc):
    table = doc.add_table(rows=1, cols=4)
    headers = ["Компонент", "Что уже есть в репозитории", "Статус для презентации", "Что показать"]
    for cell, text in zip(table.rows[0].cells, headers):
        cell.text = text
    set_repeat_header(table.rows[0])
    rows = [
        ("Студенческое мини-приложение", "React + TypeScript: onboarding, Home, Career GPS, возможности, база знаний, профиль", "Подтверждено локально", "Реальные экраны и один связный путь студента"),
        ("Административная панель", "React-панель: показатели, база знаний, возможности, карьерные роли, аналитика, пользователи", "Подтверждено локально", "Публикация возможности и аналитика"),
        ("Серверный API", "Django/DRF, JWT, PostgreSQL, сервисы подбора, Career GPS, базы знаний, уведомлений", "Реализовано", "Схема API и ключевые endpoints"),
        ("Контроль доступа и данные", "Роли, tenant-контекст университета, изоляция данных, синтетические demo-данные", "Реализовано / проверить на финальном прогоне", "Короткое пояснение без показа секретов"),
        ("MAX mock", "Уведомление создается идемпотентно и получает статус simulated", "Проверено локально", "PASS-сценарий и явная маркировка simulated"),
        ("MAX real", "Адаптер и webhook-контур есть; нужна публичная HTTPS-среда, токен и реальная доставка", "Не заявлять как завершенную доставку", "Янтарный статус и список условий проверки"),
    ]
    for i, row in enumerate(rows):
        cells = table.add_row().cells
        for cell, text in zip(cells, row):
            cell.text = text
        if i in (0, 1, 2, 3, 4):
            shade(cells[2], GREEN)
        else:
            shade(cells[2], AMBER)
    format_table(table)
    return table


SLIDES = [
    {
        "num": "1",
        "title": "Титульный слайд и техническая информация для проверки",
        "purpose": "Выполнить обязательное требование конкурса и сразу дать жюри проверяемую точку входа.",
        "thesis": "UniPath MAX - воспроизводимый MVP цифрового навигатора студента от профиля и skill gap до релевантной возможности.",
        "content": [
            "Название: UniPath MAX.",
            "Короткий дескриптор: персональный навигатор студента в MAX.",
            "Ссылка на работающий бот или мини-приложение в MAX - заполнить перед финальным экспортом.",
            "Ссылка на GitHub и commit hash финальной версии.",
            "API, OpenAPI, DATA-API и локальные адреса проверки.",
            "Demo-учетки: student@demo.local, admin@demo.local, editor@demo.local; пароль demo12345.",
            "Короткий порядок запуска через Docker.",
        ],
        "visual": "Название крупно слева; справа - компактная строка ссылок/статусов и небольшой скриншот MAX mini app или студенческого Home. Если реального MAX еще нет, не имитировать его: показать локальный экран и подпись «локальный mock-режим». ",
        "proof": "Слайд служебный и не должен перегружаться объяснением продукта. Секреты, токены и приватные ключи не показывать.",
        "notes": "Первый слайд по правилам конкурса - технический; он одновременно выполняет роль титульного.",
    },
    {
        "num": "2",
        "title": "Команда и executive summary",
        "purpose": "Показать, кто отвечает за продукт, и за 20 секунд объяснить решение.",
        "thesis": "Команда связала продуктовую проблему студента, сервисную задачу университета и рабочий end-to-end MVP.",
        "content": [
            "Название и краткое обещание продукта в 1-2 предложениях.",
            "4 карточки команды: ФИО + роль + конкретная зона вклада. Имена взять у команды; не придумывать.",
            "Рекомендуемые роли: product/problem framing; backend/API; frontend/UX; data/QA/DevOps - адаптировать к фактическому составу.",
            "Одна строка о главной демонстрации: подписка -> публикация -> релевантное уведомление -> возврат к действию.",
        ],
        "visual": "Четыре лаконичные карточки без стоковых портретов: имя, роль, вклад. Внизу - горизонтальный product promise и один мини-скриншот.",
        "proof": "Имена и роли нужно заменить до передачи дизайнеру; в репозитории сведений о составе команды нет.",
        "notes": "Не делать слайд резюме навыков. Жюри важно понять зоны ответственности и единый продуктовый замысел.",
    },
    {
        "num": "3",
        "title": "Целевая аудитория чат-бота и ее потребности",
        "purpose": "Сузить аудиторию и показать, чью конкретную ситуацию решает продукт.",
        "thesis": "Приоритетная аудитория - студенты вузов и СПО на переходе от обучения к практике, проектам и первой работе; вторичная - сотрудники университета, которые управляют контентом и возможностями.",
        "content": [
            "Персона 1: студент 1-4 курса или выпускник, которому нужно понять следующий шаг и увидеть возможности под свой профиль.",
            "Потребности студента: единая точка входа; понятная карьерная цель; skill gap; проверенные ответы; подходящие стажировки, проекты, хакатоны; своевременные уведомления.",
            "Персона 2: редактор/администратор университета.",
            "Потребности университета: управлять проверенным контентом и возможностями; задавать роли и навыки; видеть запросы, просмотры и сохранения; не работать напрямую с базой данных.",
            "Границы: не заявлять продукт как универсальный сервис для школьников, родителей и педагогов - это возможные следующие сегменты, но не текущий MVP.",
        ],
        "visual": "Две крупные персоны с короткими jobs-to-be-done: «Мне нужно понять, что делать дальше» и «Мне нужно быстро опубликовать проверенную возможность и увидеть отклик». ",
        "proof": "Слайд 11 даст внешние данные о спросе на практику и трудоустройство; на этом слайде не перегружать цифрами.",
        "notes": "Текст «чат-бот» использовать только в контексте входа и уведомлений; основная ценность реализована в mini app и API.",
    },
    {
        "num": "4",
        "title": "Проблема и переход от As Is к To Be",
        "purpose": "Связать пользовательскую боль, текущий процесс и продуктовый эффект.",
        "thesis": "Сейчас студент собирает следующий шаг из разрозненных источников и субъективных подсказок; UniPath MAX связывает профиль, проверенные данные и конкретное действие.",
        "content": [
            "As Is: информация университета распределена по каналам; возможности легко пропустить; рекомендации не объясняют соответствие; администратор не видит полный спрос.",
            "To Be: профиль один раз заполняется в mini app; Career GPS показывает готовность и gaps; подбор объясняет match; verified knowledge не выдумывает ответы; подписка возвращает пользователя к релевантному действию.",
            "Гипотеза эффекта: уменьшается время от вопроса/интереса до следующего действия; повышается доля осмысленных просмотров, сохранений и подписок.",
            "Важно: тезис о разрозненности информации подать как проблему процесса и гипотезу пилота, а не как измеренный факт текущего исследования команды.",
        ],
        "visual": "Сравнение в две колонки As Is / To Be с одной центральной стрелкой и без длинных абзацев. Добавить 3-4 шага текущего пути и 3-4 шага нового пути.",
        "proof": "Подкрепить внешний слайд 11; внутреннюю проверку проблемы продолжить через top queries, unanswered queries и события аналитики.",
        "notes": "Не использовать абстрактное «AI решит образование». Начать с конкретной точки воздействия: следующий шаг студента.",
    },
    {
        "num": "5",
        "title": "Решение и ценность продукта",
        "purpose": "Объяснить, что именно делает UniPath MAX и какой результат получает пользователь.",
        "thesis": "UniPath MAX соединяет MAX, студенческое mini app, университетскую базу знаний, карьерную логику, каталог возможностей и административную панель.",
        "content": [
            "Для студента: профиль, Career GPS, match возможностей, подписки, знания, уведомления.",
            "Для университета: проверенный контент, возможности, карьерные роли и навыки, аналитика.",
            "Ожидаемый результат: студент понимает, что делать дальше; университет получает управляемый канал полезного контента и обратной связи.",
            "Ключевой принцип: ядро ценности работает без внешней LLM - на собственных данных и детерминированной логике.",
        ],
        "visual": "Одна схема с пользователем в центре: MAX -> mini app -> API -> сервисы -> админ-панель. Не превращать в техническую архитектуру - детали будут на слайде 10.",
        "proof": "Основа взята из README, docs/architecture.md и текущих маршрутов frontend-student/frontend-admin.",
        "notes": "Показать результат для обеих сторон, но главным героем оставить студента.",
    },
    {
        "num": "6",
        "title": "Ключевые фичи и пользовательский сценарий студента",
        "purpose": "Показать один законченный сценарий вместо каталога экранов.",
        "thesis": "Данные профиля реально проходят через цепочку: onboarding -> Career GPS -> explainable matching -> подписка -> уведомление.",
        "content": [
            "1. Студент входит через MAX или demo-login.",
            "2. Выбирает университет, институт, программу, курс, интересы, навыки и карьерную цель.",
            "3. Видит readiness score, strengths, gaps и next actions.",
            "4. Открывает возможность с match percentage, причинами совпадения и недостающими навыками.",
            "5. Сохраняет возможность и создает подписку на тему, например Backend, практика или хакатоны.",
            "6. Возвращается к релевантному действию после публикации.",
        ],
        "visual": "Лента из 5-6 реальных экранов с короткими подписями и одной выделенной стрелкой «данные профиля влияют на следующий экран».",
        "proof": "Данные сценария подтверждены README, DEMO_TEST_SCENARIO.md и маршрутами frontend-student/src/pages.",
        "notes": "Каждый экран должен быть крупным и читаемым; не ставить 6 полноразмерных интерфейсов в миниатюрах.",
    },
    {
        "num": "7",
        "title": "Проверенная база знаний и безопасный fallback",
        "purpose": "Отдельно показать доверие к информации университета и корректное поведение при отсутствии ответа.",
        "thesis": "Система показывает только опубликованные и проверенные материалы; при отсутствии подтверждения не придумывает ответ, а предлагает обратиться в ответственное подразделение.",
        "content": [
            "Поиск по запросу «производственная практика».",
            "Карточка результата: источник/ответственное подразделение, verified status, дата обновления или актуальности, аудитория.",
            "Неизвестный запрос: понятный безопасный ответ и эскалация.",
            "Для администратора: создание, редактирование и публикация knowledge items.",
        ],
        "visual": "Split-screen: слева хороший результат с зеленым verified; справа fallback с нейтральным/янтарным статусом. На скриншоте читаются источник и дата.",
        "proof": "Подтверждено KnowledgeSearchService и экранами Knowledge/KnowledgeDetail; не добавлять обещания генеративного ответа.",
        "notes": "Это сильная UX-деталь для оценки обоснованности и работы с официальными данными.",
    },
    {
        "num": "8",
        "title": "Сценарий уведомления через MAX",
        "purpose": "Показать, зачем в решении MAX и где возникает дополнительная пользовательская ценность.",
        "thesis": "MAX - не просто контейнер mini app: он возвращает студента к конкретной возможности, когда университет публикует релевантный контент.",
        "content": [
            "Студент создает активную подписку на тему.",
            "Администратор публикует подходящую возможность.",
            "Сервис находит совпадение и создает уведомление по идемпотентному ключу.",
            "В mock-режиме уведомление хранится локально со статусом simulated.",
            "В real-режиме сообщение отправляется через MAX API и может содержать open_app-кнопку возврата к opportunity.",
            "Повторная публикация не должна создавать дубль.",
        ],
        "visual": "Четкая цепочка 1-2-3-4-5; если real MAX не проверен, последнюю часть выделить янтарным цветом и подписать «условие финальной проверки». ",
        "proof": "Локальная идемпотентность и mock-статус описаны в README, DEMO_TEST_SCENARIO.md и apps/notifications/services.py.",
        "notes": "Не показывать simulated как доставленное сообщение в реальном чате.",
    },
    {
        "num": "9",
        "title": "Технические требования к итоговому решению",
        "purpose": "Сделать видимыми требования конкурса и текущую готовность продукта.",
        "thesis": "MVP должен быть воспроизводим, проверяем и честно отделять локальную демонстрацию от внешней доставки MAX.",
        "content": [
            "Доступ к работающему MAX-боту/mini app или понятный локальный demo-путь.",
            "Docker Compose для запуска backend, student frontend, admin frontend и PostgreSQL.",
            "REST API с OpenAPI; DATA-API.yaml с проверяемыми сценариями, ролями, статус-кодами и ожидаемыми ответами.",
            "Seed/demo-данные и тестовые учетные записи; данные обозначить как синтетические.",
            "JWT-аутентификация, роли, tenant isolation, безопасное хранение секретов вне репозитория.",
            "Проверяемый путь: login/onboarding -> Career GPS -> opportunity matching -> subscription -> publish -> notification.",
            "Для real MAX: токен, публичный HTTPS, webhook, MAX_OPEN_APP_TARGET и финальная репетиция доставки.",
        ],
        "visual": "Чек-лист из трех колонок: требование / как проверить / статус. Зеленым отмечать локально проверенное; янтарным - внешне зависимое.",
        "proof": "При подготовке финального deck обновить статусы по свежему запуску на том commit hash, который указан на слайде 1.",
        "notes": "Не помещать в презентацию реальные токены, API-ключи и приватные URL.",
    },
    {
        "num": "10",
        "title": "Архитектура, логика работы и направления масштабирования",
        "purpose": "Показать цельную техническую реализацию и реалистичный путь роста.",
        "thesis": "Модульный монолит дает простой запуск и транзакционную целостность MVP, а сервисные границы оставляют путь к выделению нагруженных доменов.",
        "content": [
            "React Student UI и React Admin UI -> Django REST API -> PostgreSQL.",
            "Сервисный слой: Career GPS, Opportunity Matching, Knowledge Search, Analytics, Notifications и MAX adapter.",
            "Логика подбора: профиль и StudentSkill -> сравнение с требованиями роли/возможности -> score, reasons, gaps.",
            "Логика знаний: поиск по verified records -> результат или safe fallback.",
            "Логика уведомлений: активная подписка + совпадение -> idempotency key -> mock/real provider.",
            "Масштабирование: несколько университетов через tenant-контекст; затем индексы, managed reference data, асинхронные уведомления; при росте нагрузки - выделение matching/search/analytics/notifications.",
        ],
        "visual": "Схема из 3 уровней с цветовой легендой: интерфейсы, API/сервисы, данные/интеграции. Внизу - стрелка «один вуз -> несколько вузов -> выделение отдельных доменов». ",
        "proof": "Опора на docs/architecture.md, backend/apps/*, backend/config/urls.py и README.",
        "notes": "Не рисовать микросервисную архитектуру - текущий MVP является модульным монолитом.",
    },
    {
        "num": "11",
        "title": "Исследования, подтверждающие востребованность",
        "purpose": "Показать, что продуктовая гипотеза имеет внешние основания, и не выдавать допущения за измеренный эффект.",
        "thesis": "Студентам важны практика и выход на рынок труда, а образовательные и карьерные траектории неоднородны - значит, ценность персонального и своевременного навигатора правдоподобна.",
        "content": [
            "Опрос Минпросвещения/ИРПО, 2024: 96,7 тыс. студентов колледжей из 89 регионов; 50% отметили интересную практику и помощь в трудоустройстве как преимущество; 61,6% планируют сразу выйти на рынок труда; 55% уже работают или подрабатывают.",
            "Исследование ТрОП НИУ ВШЭ: национальная лонгитюдная панель; первая всероссийская волна - 4 893 школьника из 210 школ и 42 субъектов; на последней волне около 50% опрошенных выпускников вузов работают по специальности. Использовать как контекст сложности образовательных и карьерных траекторий.",
            "Правительство России, 2025: сервис практик и стажировок на «Работе России» развивает цифровое взаимодействие; к нему подключены более 23 тыс. организаций и более 2,6 тыс. образовательных учреждений. Это подтверждает масштаб экосистемы, а не успешность UniPath MAX.",
            "Отдельная оговорка: ни один источник не измеряет эффективность именно UniPath MAX; эффект продукта нужно проверять пилотом.",
        ],
        "visual": "Три крупных verified-цифры с подписью «внешний контекст» и короткие источники внизу. Не строить ложный график роста из несопоставимых данных.",
        "proof": "Ссылки на источники приведены в разделе «Источники» этого ТЗ и должны быть на слайде/в примечаниях к презентации.",
        "notes": "При сокращении текста оставить выборку, год и формулировку, чтобы не потерять смысл статистики.",
    },
    {
        "num": "12",
        "title": "Пилот, метрики и ожидаемый эффект",
        "purpose": "Перевести ценность из обещания в измеримый план пилота.",
        "thesis": "Первый пилот должен доказать, что студент быстрее доходит до релевантного действия, а университет видит спрос и может поддерживать актуальный контент.",
        "content": [
            "Пилот: один вуз или один институт, 1-2 приоритетных карьерных сценария, ограниченный набор редакторов и проверенных материалов.",
            "Метрики студента: onboarding completion; time to first Career GPS; доля просмотренных возможностей с match/reasons; saves; subscriptions; notification open/return rate.",
            "Метрики контента: verified answer rate; unanswered query rate; freshness; время от создания до публикации.",
            "Метрики результата: доля студентов, совершивших целевое действие после рекомендации; количество заявок/регистраций - если источник данных это позволяет.",
            "Гипотеза: персонализация и proactive notification сокращают путь до следующего действия; это не результат текущего MVP, а критерий пилота.",
        ],
        "visual": "Воронка «профиль -> полезный экран -> сохранение/подписка -> действие» и 4-5 метрик рядом. Все показатели подписать как pilot metrics.",
        "proof": "Событийная аналитика и admin analytics уже предусмотрены в проекте; числовые baseline и target нужно определить на пилоте.",
        "notes": "Не использовать вымышленные проценты конверсии.",
    },
    {
        "num": "13",
        "title": "Надежность, ограничения и честный статус",
        "purpose": "Закрыть вопросы жюри о повторяемости, безопасности и внешних зависимостях.",
        "thesis": "У продукта есть проверяемый локальный контур; внешнюю доставку MAX нужно показать только после реальной end-to-end проверки.",
        "content": [
            "Показать: тесты backend/frontend, сборки, Docker health, DATA-API smoke, OpenAPI, отсутствие дублей уведомлений.",
            "Ограничения текущего MVP: demo-данные синтетические; knowledge search детерминированный по seeded verified records; JWT refresh не полностью выведен в UX; real MAX зависит от публичного HTTPS и credentials.",
            "Статус-легенда: зеленый - проверено локально; синий - реализовано в коде; янтарный - внешняя проверка требуется; серый - направление развития.",
            "Финальная проверка real MAX: token -> webhook -> linked max_user_id -> publish -> one notification -> message -> open_app -> relevant opportunity.",
        ],
        "visual": "Чек-лист доказательств слева и блок ограничений справа. Один янтарный пункт «real MAX delivery» должен быть заметным, но не драматизированным.",
        "proof": "Статусы брать из свежего прогона; не переносить старые числа тестов без повторной проверки.",
        "notes": "Честное ограничение повышает доверие и соответствует требованиям конкурса к работе с тестовыми/смоделированными данными.",
    },
    {
        "num": "14",
        "title": "Финальный демонстрационный сценарий и call to action",
        "purpose": "Оставить у жюри ясную картину того, что нужно увидеть в защите и почему это важно.",
        "thesis": "Самая сильная история: студент подписался на карьерную тему, университет опубликовал релевантную возможность, UniPath MAX вернул студента к конкретному действию.",
        "content": [
            "Показать 7-9 шагов: вход -> профиль -> Career GPS -> opportunity match -> подписка -> admin publish -> notification -> return to app -> action.",
            "Финальная фраза: «Не набор экранов, а проверяемый маршрут от вопроса студента до следующего действия». ",
            "Внизу - QR/ссылка на demo, GitHub и контакты команды; не дублировать все технические детали первого слайда.",
        ],
        "visual": "Одна горизонтальная история с финальной рамкой вокруг последнего действия. Если real MAX не подтвержден, финальный кадр - локальный opportunity detail и подпись mock-mode.",
        "proof": "Сценарий совпадает с DEMO_TEST_SCENARIO.md; реальные ссылки добавить перед экспортом.",
        "notes": "Если нужен более короткий deck, этот слайд можно превратить в финальную часть слайда 13.",
    },
]


def build():
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Cm(1.65)
    section.bottom_margin = Cm(1.55)
    section.left_margin = Cm(1.8)
    section.right_margin = Cm(1.8)

    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = FONT
    normal._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), FONT)
    normal._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), FONT)
    normal.font.size = Pt(10.5)
    normal.font.color.rgb = BLACK
    normal.paragraph_format.space_after = Pt(5)
    normal.paragraph_format.line_spacing = 1.08
    for name, size in (("Title", 25), ("Subtitle", 13), ("Heading 1", 16), ("Heading 2", 13.2), ("Heading 3", 11.2)):
        st = styles[name]
        st.font.name = FONT
        st._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), FONT)
        st._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), FONT)
        st.font.size = Pt(size)
        st.font.color.rgb = BLACK
        st.paragraph_format.space_before = Pt(10 if name != "Title" else 0)
        st.paragraph_format.space_after = Pt(5)
        st.paragraph_format.keep_with_next = True

    # Header/footer
    header = section.header.paragraphs[0]
    header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    hr = header.add_run("UniPath MAX  /  ТЗ дизайнеру")
    set_run_font(hr, 8, color=RGBColor(100, 100, 100))
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    fr = footer.add_run("Страница ")
    set_run_font(fr, 8, color=RGBColor(100, 100, 100))
    add_page_number(footer)

    # Cover page
    p = doc.add_paragraph(style="Title")
    p.paragraph_format.space_before = Cm(3.1)
    r = p.add_run("ТЗ на презентацию решения UniPath MAX")
    set_run_font(r, 25, bold=True)
    sub = doc.add_paragraph(style="Subtitle")
    sub.paragraph_format.space_before = Pt(10)
    sr = sub.add_run("Содержание слайдов и требования к дизайнеру")
    set_run_font(sr, 13, color=RGBColor(60, 60, 60))
    add_para(doc, "Презентация в формате PDF для экспертной оценки образовательного MVP в MAX.", after=16, size=11)
    table = doc.add_table(rows=3, cols=2)
    table.rows[0].cells[0].text = "Продукт"
    table.rows[0].cells[1].text = "UniPath MAX - персональный цифровой навигатор студента"
    table.rows[1].cells[0].text = "Результат"
    table.rows[1].cells[1].text = "Понятный deck о проблеме, пользователях, сценарии, архитектуре, доказательствах и масштабе"
    table.rows[2].cells[0].text = "Подготовлено"
    table.rows[2].cells[1].text = "21 сентября 2026"
    format_table(table, header=False, alternate=True)
    shade(table.rows[0].cells[0], LIGHT_BLUE)
    shade(table.rows[1].cells[0], LIGHT_BLUE)
    shade(table.rows[2].cells[0], LIGHT_BLUE)
    add_para(doc, "Рамка конкурса", style="Heading 2", after=4)
    add_para(doc, "В приложенном документе «Образовательные решения.pdf» указано, что первый слайд должен содержать техническую информацию для проверки, а со второго слайда презентация должна раскрывать команду, аудиторию, проблему, решение, ожидаемый эффект, архитектуру, данные, масштабирование, ограничения и источники. Это ТЗ учитывает эти требования и дополняет прошлогодний минимум блоками про команду, аудиторию, исследовательские основания и пилотные метрики.", after=0)
    doc.add_page_break()

    # Intro
    add_section_heading(doc, "1. Что нужно получить", 1)
    add_para(doc, "Нужна продуктовая презентация на 12-14 слайдов в PDF, которая показывает работающий MVP UniPath MAX и один связный путь пользователя. Главная мысль: продукт помогает студенту понять следующий шаг - закрыть skill gap, найти релевантную возможность, получить проверенную информацию и вернуться к действию через MAX.")
    add_para(doc, "Презентация должна быть доказательной. Уже реализованное показываем как реализованное; локальный mock-режим обозначаем явно; реальную доставку через MAX не заявляем до финальной проверки токена, публичного HTTPS, webhook и возврата в mini app.")
    add_section_heading(doc, "2. Краткий профиль проекта", 1)
    add_para(doc, "UniPath MAX объединяет React mini app для студента, React-панель администратора и Django REST API с PostgreSQL. Студент проходит onboarding, получает Career GPS, видит explainable matching возможностей, ищет проверенные материалы базы знаний, подписывается на темы и получает уведомление при публикации релевантной возможности. Университет управляет контентом, возможностями, карьерными ролями и аналитикой.")
    add_status_table(doc)
    add_para(doc, "Граница утверждений", style="Heading 2", after=4)
    add_bullets(doc, [
        "Факт проекта: в репозитории есть код, маршруты, модели, сервисы, OpenAPI, DATA-API и сценарий локальной демонстрации.",
        "Проверка: конкретные PASS-цифры и состояние Docker нужно обновить на финальном commit hash перед экспортом PDF.",
        "Внешняя зависимость: реальная доставка MAX требует публичного окружения и учетных данных; локальный статус simulated нельзя показывать как sent.",
        "Предложение пилота: метрики эффекта и целевые значения не являются текущим результатом и должны быть обозначены как план проверки.",
    ])

    add_section_heading(doc, "3. Нарратив и визуальные правила", 1)
    add_para(doc, "Ритм презентации: проблема -> пользователь -> решение -> демонстрация -> техническое доказательство -> исследование -> пилот и масштабирование -> честные ограничения. На каждом слайде должен быть один главный тезис и один ведущий визуальный объект.")
    add_bullets(doc, [
        "Формат: 16:9, PDF, целевая область 1920x1080 или 13.333 x 7.5 in.",
        "Язык: русский; допускаются устоявшиеся названия Career GPS, match, skill gap, MAX, API и Docker, но подписи интерфейса - русские.",
        "Стиль: современная продуктовая презентация для EdTech; белый фон, темный текст, синий акцент MAX, зеленый для подтвержденного, янтарный для внешней проверки.",
        "Материалы: реальные скриншоты текущего интерфейса, простые схемы и короткие подписи; не использовать абстрактные стоковые иллюстрации как доказательство продукта.",
        "Читаемость: один экран или схема должны читаться на защите; не собирать мозаику из мелких скриншотов и не помещать длинные абзацы на слайды.",
        "Данные: каждая цифра слайда 11 должна иметь источник, год, выборку и короткую подпись о границах применимости.",
        "Скриншоты: demo-логины допустимы на техническом слайде; токены, приватные ключи и секреты не показывать.",
    ])
    add_section_heading(doc, "4. Статусы, которые должны быть видны дизайнеру", 2)
    status = doc.add_table(rows=1, cols=3)
    for cell, text in zip(status.rows[0].cells, ["Статус", "Значение", "Визуальный код"]):
        cell.text = text
    set_repeat_header(status.rows[0])
    for row in [("Проверено", "Есть локальный прогон/тест/сценарий", "Зеленый"), ("Реализовано", "Есть в коде, но факт проверки нужно обновить", "Синий"), ("Требует внешней проверки", "Зависит от MAX token, HTTPS или реального сервиса", "Янтарный"), ("План пилота", "Будущая метрика или направление развития", "Серый")]:
        cells = status.add_row().cells
        for cell, text in zip(cells, row):
            cell.text = text
        shade(cells[0], GREEN if row[0] == "Проверено" else AMBER if row[0] == "Требует внешней проверки" else LIGHT_BLUE)
    format_table(status)

    doc.add_page_break()
    add_section_heading(doc, "5. Содержание слайдов", 1)
    add_para(doc, "Ниже для каждого слайда указаны цель, тезис, обязательное содержание, ведущий визуал, доказательство и заметки дизайнеру. Текст на слайде можно сокращать, но смысл и границу статусов сохранять.")

    for slide in SLIDES:
        add_section_heading(doc, f"Слайд {slide['num']}. {slide['title']}", 2)
        add_field_table(doc, [
            ("Цель", slide["purpose"], None),
            ("Главный тезис", slide["thesis"], LIGHT_BLUE),
            ("Обязательное содержание", "\n".join(f"• {x}" for x in slide["content"]), None),
            ("Ведущий визуал", slide["visual"], None),
            ("Доказательство и источники", slide["proof"], None),
            ("Заметка дизайнеру", slide["notes"], AMBER if "не заявлять" in slide["notes"].lower() or "не проверен" in slide["notes"].lower() else None),
        ])
        add_para(doc, "", after=2)

    add_section_heading(doc, "6. Что нужно подготовить до дизайна", 1)
    prep = doc.add_table(rows=1, cols=4)
    for cell, text in zip(prep.rows[0].cells, ["Материал", "Источник", "Для каких слайдов", "Статус"]):
        cell.text = text
    set_repeat_header(prep.rows[0])
    prep_rows = [
        ("Имена, роли и фото/аватары команды", "Команда", "2", "Заполнить"),
        ("URL MAX-бота/mini app и commit hash", "Финальная среда", "1, 14", "Заполнить перед экспортом"),
        ("Студенческие скриншоты", "frontend-student", "1, 5, 6, 7, 8, 14", "Снять на demo-данных"),
        ("Админские скриншоты", "frontend-admin", "5, 8, 9, 13", "Снять на demo-данных"),
        ("PASS DATA-API, Docker health, тесты и build", "Свежий прогон на commit hash", "1, 9, 13", "Обновить числа"),
        ("Скрин MAX-сообщения", "Реальный MAX или mock", "8, 13, 14", "Показывать real только после проверки"),
        ("Диаграмма архитектуры", "docs/architecture.md", "5, 10", "Перерисовать в едином стиле"),
        ("Исследовательские цифры и ссылки", "Источники ниже", "4, 11", "Поставить сноски"),
    ]
    for i, row in enumerate(prep_rows):
        cells = prep.add_row().cells
        for cell, text in zip(cells, row):
            cell.text = text
        if "Заполнить" in row[3] or "Обновить" in row[3]:
            shade(cells[3], AMBER)
    format_table(prep)
    add_section_heading(doc, "7. Минимальная последовательность демонстрации", 1)
    add_numbered(doc, [
        "Открыть студенческий контур и показать вход/профиль.",
        "Показать выбранную карьерную цель, readiness score, strengths и gaps.",
        "Открыть возможность с match percentage, reasons и gaps.",
        "Создать или показать подписку на Backend/практику/хакатоны.",
        "В админ-панели опубликовать релевантную возможность.",
        "Показать одно уведомление без дубля; в mock-режиме - статус simulated.",
        "Если real MAX проверен, открыть сообщение и вернуться к нужной возможности; если нет, честно показать локальную границу.",
        "Завершить поиском проверенной статьи и неизвестного запроса с fallback.",
    ])
    add_section_heading(doc, "8. Источники и подписи", 1)
    add_para(doc, "Источники проекта: README.md, docs/architecture.md, DEMO_TEST_SCENARIO.md, openapi.yaml, DATA-API.yaml, PRESENTATION_BRIEF_RU.txt; приложенный файл «Образовательные решения.pdf», слайды/страницы 6-19. В итоговом deck ссылки можно вынести в мелкие сноски или на backup-слайд, но цифры должны быть читаемыми.")
    sources = [
        ("Минпросвещения России / ИРПО. Опрос студентов СПО, 2024: 96,7 тыс. респондентов, 89 регионов; практика и помощь в трудоустройстве, планы выхода на рынок труда и занятость во время учебы.", "https://edu.gov.ru/press/8721/pochti-tri-chetverti-studentov-organizaciy-spo-planiruyut-rabotat-po-specialnosti/"),
        ("НИУ ВШЭ. Исследование «Траектории в образовании и профессии» (ТрОП): национальная лонгитюдная панель и данные об образовательно-карьерных траекториях.", "https://trec.hse.ru/anniversary/"),
        ("Правительство России. Цифровизация практик и стажировок на портале «Работа России», 2025.", "https://government.ru/news/58296/"),
        ("Росстат. Трудовые ресурсы, занятость и безработица; раздел с материалами по трудоустройству выпускников.", "https://rosstat.gov.ru/labour_force"),
    ]
    st = doc.add_table(rows=1, cols=2)
    for cell, text in zip(st.rows[0].cells, ["Источник и что подтверждает", "Ссылка"]):
        cell.text = text
    set_repeat_header(st.rows[0])
    for title, url in sources:
        cells = st.add_row().cells
        cells[0].text = title
        cells[1].text = ""
        p = cells[1].paragraphs[0]
        add_hyperlink(p, url, url)
    format_table(st)
    add_para(doc, "Примечание по доказательности", style="Heading 2", after=4)
    add_para(doc, "Внешние исследования подтверждают актуальность карьерной навигации, практики и своевременной связи с возможностями, но не доказывают эффект именно UniPath MAX. Эффект проекта следует проверять на пилоте через события аналитики и заранее определенные метрики.", after=0)

    doc.core_properties.title = "ТЗ на презентацию решения UniPath MAX"
    doc.core_properties.subject = "Содержание PDF-презентации и требования к дизайнеру"
    doc.core_properties.author = "Codex"
    doc.core_properties.comments = "Prepared from repository materials, attached contest brief and current public research sources."
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    print(OUT)


if __name__ == "__main__":
    build()
