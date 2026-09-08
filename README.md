# Payment Processing Service

Асинхронный микросервис для обработки платежей: принимает запрос на оплату,
эмулирует обработку через внешний платёжный шлюз и уведомляет клиента о
результате через webhook. Построен на паттерне **Transactional Outbox** с
гарантированной доставкой событий через RabbitMQ, retry с экспоненциальной
задержкой и Dead Letter Queue для окончательно неудачных попыток.

## Содержание

- [Архитектура](#архитектура)
- [Стек технологий](#стек-технологий)
- [Быстрый старт](#быстрый-старт)
- [Команды Makefile](#команды-makefile)
- [API](#api)
- [Как это работает: outbox → RabbitMQ → consumer → webhook](#как-это-работает-outbox--rabbitmq--consumer--webhook)
- [Retry и Dead Letter Queue](#retry-и-dead-letter-queue)
- [Как проверить руками](#как-проверить-руками)
- [Структура проекта](#структура-проекта)
- [Известные компромиссы](#известные-компромиссы)

## Архитектура

Проект построен по **hexagonal architecture** (ports & adapters) с полной
изоляцией домена от инфраструктуры:

```
core/       - домен: dataclass-сущности, enum'ы, Protocol-интерфейсы
              (порты), бизнес-логика сервисов. Не знает про SQLAlchemy,
              FastStream, httpx - только абстракции.
outbound/   - driven-адаптеры: реализации портов из core, которые
              ОБРАЩАЮТСЯ к инфраструктуре (БД через SQLAlchemy, RabbitMQ
              publisher, HTTP-клиент для webhook).
inbound/    - driving-адаптеры: точки входа, которые ИНИЦИИРУЮТ вызов
              домена (HTTP-роутеры, RabbitMQ consumer-хендлеры).
main/       - composition root: сборка зависимостей, конфигурация,
              entrypoints процессов (FastAPI-приложение, consumer).
```

## Стек технологий

- **FastAPI** + **Pydantic v2** - HTTP API
- **SQLAlchemy 2.0** (async) + **Alembic** - работа с БД и миграции
- **PostgreSQL 18**
- **RabbitMQ** + **FastStream** - брокер сообщений
- **httpx** - отправка webhook-уведомлений
- **Docker Compose** - оркестрация

## Быстрый старт

### Требования

- Docker и Docker Compose
- `make`

### 1. Настройка окружения

Проект генерирует `.env` автоматически из двух файлов:

- **`env.example`** - несекретные настройки, уже в репозитории
- **`.secrets`** - пароли и ключи, создаётся вручную, **не коммитится**

Создайте `.secrets` в корне проекта:

```bash
# Postgres
POSTGRES__USER=postgres
POSTGRES__PASSWORD=password

# RabbitMQ
RABBITMQ__USER=rabbitmq_user
RABBITMQ__PASSWORD=password

# App
APP__API_KEY=your-secret-api-key
```

Значения можно оставить любыми произвольными - сервис не проверяет их
осмысленность, только использует для подключения контейнеров друг к другу
и для проверки `X-API-Key` в запросах.

### 2. Запуск

```bash
make up
```

Это сгенерирует `.env` из `env.example` + `.secrets`, соберёт образ и
поднимет весь стек: `db_pg`, `rabbitmq`, `migrations` (применит схему БД и
завершится), `app` (HTTP API + фоновая публикация событий), `consumer`
(обработка платежей).

Для запуска в фоне:

```bash
make upd
```

### 3. Проверка

API поднимется на `http://localhost:8000`. Документация OpenAPI -
`http://localhost:8000/docs`. RabbitMQ management UI -
`http://localhost:15672` (логин/пароль - из `.secrets`).

```bash
make logs
```

## Команды Makefile

| Команда | Описание |
|---|---|
| `make up` | Собрать и поднять весь стек (foreground) |
| `make upd` | Собрать и поднять весь стек (detached) |
| `make just_up` | Поднять без пересборки |
| `make down` | Остановить и удалить контейнеры |
| `make stop` / `make start` | Остановить/запустить без пересоздания |
| `make restart` | Перезапустить контейнеры |
| `make logs` | Логи всех сервисов (follow) |
| `make logs-app` | Логи API-процесса |
| `make logs-consumer` | Логи consumer-процесса |
| `make logs-migrations` | Логи применения миграций |
| `make logs-db` | Логи PostgreSQL |
| `make logs-rabbitmq` | Логи RabbitMQ |
| `make ps` | Статус всех контейнеров |
| `make migration m="описание"` | Сгенерировать новую Alembic-миграцию |
| `make prune` | Очистить неиспользуемые Docker-ресурсы |

## API

Все бизнес-эндпоинты (`/api/v1/*`) требуют заголовок `X-API-Key` со
значением из `APP__API_KEY` (см. `.secrets`); сравнение выполняется
constant-time (`secrets.compare_digest`), чтобы не давать возможности
подобрать ключ по времени ответа. `/health` и `/docs` открыты (см.
[Известные компромиссы](#известные-компромиссы)).

### Создание платежа

```
POST /api/v1/payments
```

**Заголовки:**

| Заголовок | Обязателен | Описание |
|---|---|---|
| `X-API-Key` | да | Статический ключ аутентификации |
| `Idempotency-Key` | да | Уникальный ключ для защиты от дублей |

**Тело запроса:**

```json
{
  "amount": "100.50",
  "currency": "RUB",
  "description": "test payment",
  "webhook_url": "https://webhook.site/your-unique-id",
  "meta_data": {"order_id": "123"}
}
```

`currency` - одно из `RUB`, `USD`, `EUR`. `amount` - положительное число
с точностью до 2 знаков после запятой (до 18 значащих цифр,
бесконечность/NaN отклоняются). `description` и `meta_data` -
опциональные. `webhook_url` - валидный HTTP(S) URL.

**Пример:**

```bash
curl -X POST http://localhost:8000/api/v1/payments \
  -H "X-API-Key: your-secret-api-key" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: test-key-001" \
  -d '{
    "amount": "100.50",
    "currency": "RUB",
    "description": "test payment",
    "webhook_url": "https://webhook.site/your-unique-id",
    "meta_data": {"order_id": "123"}
  }'
```

**Ответ `202 Accepted`:**

```json
{
  "payment_id": 1,
  "status": "pending",
  "created_at": "2026-09-08T04:27:47.609477Z"
}
```

Повторный запрос с тем же `Idempotency-Key` вернёт **тот же** платёж, а
не создаст дубль - включая при одновременных (гоночных) запросах: защита
реализована через `UniqueConstraint` в БД и корректную обработку
`IntegrityError` на уровне репозитория.

### Получение платежа

```
GET /api/v1/payments/{payment_id}
```

```bash
curl http://localhost:8000/api/v1/payments/1 \
  -H "X-API-Key: your-secret-api-key"
```

**Ответ `200 OK`:**

```json
{
  "id": 1,
  "idempotency_key": "test-key-001",
  "created_at": "2026-09-06T12:55:54.781133Z",
  "processed_at": "2026-09-06T12:56:01.420120Z",
  "amount": "100.50",
  "currency": "RUB",
  "webhook_url": "https://webhook.site/your-unique-id",
  "description": "test payment",
  "meta_data": {"order_id": "123"},
  "status": "succeeded"
}
```

`404 Not Found`, если платёж с таким `id` не существует.

## Как это работает: outbox → RabbitMQ → consumer → webhook

1. `POST /payments` создаёт `Payment` и `OutboxEvent` **одной транзакцией**
   в БД. RabbitMQ на этом шаге не участвует - если он временно
   недоступен, платёж всё равно надёжно сохранён.
2. Фоновая задача внутри `app`-процесса (`outbox_relay`) каждую секунду
   читает необработанные `outbox_events` и публикует их в RabbitMQ
   (exchange `payments`, routing key `payments.new`), затем помечает
   событие как `SENT`.
3. `consumer`-процесс подписан на очередь `payments.new`. Получив
   сообщение, он:
   - атомарно переводит платёж из `pending` в `processing`
     (`UPDATE ... WHERE status = 'pending'` с проверкой затронутых строк) -
     если платёж уже не `pending` (обрабатывается параллельным
     consumer'ом или повторной доставкой того же сообщения), обработка
     прекращается здесь же, без повторного списания;
   - эмулирует обращение к платёжному шлюзу (задержка 2–5 сек, 90%
     успех / 10% отказ);
   - обновляет статус на `succeeded`/`failed` - этот шаг коммитится
     отдельно и независимо от следующего;
   - отправляет webhook на `webhook_url` из платежа.
4. Если webhook не удалось отправить - статус платежа уже надёжно
   зафиксирован (шаг 3 не откатывается вместе с ошибкой webhook), а
   retry повторяет только доставку уведомления, не вызывая шлюз заново.
   Если платёж по каким-то причинам не найден или уже в терминальном
   статусе - обработка идёт по retry-логике ниже.

`app` и `consumer` - два независимых процесса на одном образе, что
позволяет масштабировать и перезапускать их независимо (см. `docker-compose.yml`).

## Retry и Dead Letter Queue

RabbitMQ не имеет встроенного механизма отложенного retry, поэтому
задержка реализована через топологию TTL-очередей ("парковок"):

```
payments.new ──(ошибка)──▶ payments.retry.1 (TTL 2s)
                                  │ TTL истёк → dead-letter обратно
                                  ▼
                           payments.new ──(ошибка)──▶ payments.retry.2 (TTL 4s)
                                                              │
                                                              ▼
                                                       payments.new ──(ошибка)──▶ payments.retry.3 (TTL 8s)
                                                                                         │
                                                                                         ▼
                                                                                  payments.dlq
```

Номер текущей попытки хендлер несёт в собственном заголовке
`x-retry-attempt`, который явно проставляется при каждой повторной
публикации. RabbitMQ действительно ведёт свой заголовок `x-death` при
dead-lettering, но он не подходит для подсчёта попыток в этой схеме: raw
`x-death` группируется по паре (очередь, причина) и не накапливает
историю так, как нужно при явной публикации в новую очередь на каждый
retry - поэтому счётчик хранится и передаётся отдельным полем.

После 3 неудачных попыток сообщение публикуется в `payments.dlq`
(exchange `payments.dlx`), где отдельный хендлер логирует финальный
провал платежа.

Полный цикл (задержки экспоненциально растут: 2с → 4с → 8с) занимает
около 14 секунд с момента первой ошибки до попадания в DLQ.

## Как проверить руками

### Успешный сценарий с реальным webhook

1. Откройте [webhook.site](https://webhook.site) - получите уникальный
   URL.
2. Создайте платёж с этим URL в поле `webhook_url`.
3. Через 2–5 секунд в открытой вкладке webhook.site появится POST-запрос
   с телом вида `{"payment_id": ..., "status": "succeeded", ...}`
   (или `"failed"` - 10% вероятность, эмуляция шлюза).

### Проверка retry и DLQ

Укажите заведомо нерабочий `webhook_url`, например:

```json
"webhook_url": "https://httpbin.org/status/500"
```

```bash
make logs-consumer
```

В логах будет видно всю цепочку:

```
Payment N scheduled for retry 1
Payment N scheduled for retry 2   (~2 сек спустя)
Payment N scheduled for retry 3   (~4 сек спустя)
Payment N moved to DLQ after 3 attempts   (~8 сек спустя)
Payment N permanently failed after all retry attempts
```

### Проверка идемпотентности при гонке

```bash
for i in 1 2; do
  curl -X POST http://localhost:8000/api/v1/payments \
    -H "X-API-Key: your-secret-api-key" \
    -H "Content-Type: application/json" \
    -H "Idempotency-Key: race-test-001" \
    -d '{"amount": "50.00", "currency": "RUB", "webhook_url": "https://webhook.site/x"}' &
done
wait
```

Оба запроса должны вернуть один и тот же `payment_id` без ошибок 500.

## Структура проекта

```
src/
├── core/                      # Домен - не зависит от инфраструктуры
│   └── payments/
│       ├── models/             # dataclass-сущности, enum'ы
│       ├── interfaces.py        # Protocol-порты
│       ├── services/           # бизнес-логика
│       └── exceptions.py
├── outbound/                   # Driven-адаптеры (обращаются к инфре)
│   ├── database/                # SQLAlchemy-модели, репозитории, сессии
│   ├── rabbit_mq/                # broker, топология, publisher, relay
│   ├── payment_gateway/          # эмулятор платёжного шлюза
│   └── webhook/                  # HTTP-клиент для webhook
├── inbound/                    # Driving-адаптеры (инициируют вызов домена)
│   ├── http/                    # роутеры, схемы, зависимости FastAPI
│   └── rabbit_mq/
│       └── handlers/             # consumer-хендлеры
└── main/                       # Composition root
    ├── config/                  # settings, logging
    ├── setup/                   # сборка фоновых задач
    ├── run.py                   # entrypoint FastAPI-приложения
    └── run_consumer.py          # entrypoint consumer-процесса
```

## Известные компромиссы

Эти решения сознательные и продиктованы текущим масштабом проекта - при
росте нагрузки их стоило бы пересмотреть в указанную сторону:

- **Outbox relay** - фиксированный батч (50 событий) с опросом раз в
  секунду. При кратно большей нагрузке задержка публикации будет расти; 
- **Retry-топология** - конкретные TTL (2/4/8 сек) подобраны для
  удобства демонстрации и тестирования
- **Consumer без ручного prefetch/concurrency-тюнинга** - обрабатывает
  сообщения последовательно; для повышения throughput потребуется
  настройка `prefetch_count` и/или несколько инстансов consumer'а
  (топология уже поддерживает competing consumers на одной очереди).
- **Повторная обработка при восстановлении зависших платежей** -
  `StaleProcessingReaper` возвращает платежи, застрявшие в `processing`
  дольше `PROCESSING_LEASE_SECONDS`, обратно в оборот через outbox. Если
  предыдущий обработчик был жив, но медленен (GC-пауза, сетевой лаг
  дольше lease), возможен повторный вызов эмулятора шлюза для одного
  платежа. Двойного webhook при этом не будет (переход в терминальный
  статус защищён `expected_current_status`), но на реальном шлюзе
  потребовался бы ключ идемпотентности к самому шлюзу. Lease (30 сек)
  выбран заведомо больше максимального времени обработки (5 сек).
- **`OutboxStatus.FAILED` не используется relay'ем** - ошибка публикации
  логируется, а событие остаётся `PENDING` и будет повторно подхвачено
  на следующей итерации без ограничения числа попыток. Для транзиентных
  сбоев брокера это разумное поведение; отслеживание "зависших" событий
  потребовало бы отдельного счётчика попыток и алертинга.
- **DLQ-хендлер только логирует** сообщения. Для разбора/replay
  окончательно упавших платежей в проде очередь `payments.dlq` стоило бы
  не вычитывать автоматически либо складывать её содержимое в отдельную
  таблицу.
- **Ретенция outbox** - обработанные (`SENT`) события не удаляются;
  на длинной дистанции нужна периодическая очистка/архивация.
