## Выложил в open-source свой SEO-стек

Последний год я строил внутренние инструменты для SEO — мониторинг позиций, проверка цитирования в AI, технический аудит. Решил оформить это в один CLI-тул и выложить на GitHub.

**Searchstack** — open-source SEO / AEO / GEO стек для фаундеров.

### Что он делает

SEO изменился. Теперь мало быть на первой странице Google — нужно быть видимым в AI-поиске: Google AI Overview, ChatGPT, Perplexity, Claude, Grok.

Searchstack — это один CLI который покрывает все три слоя:

**SEO (классический Google):**
- Позиции, клики, CTR из Google Search Console
- Keyword research — подбор ключевых слов с volumes
- Анализ конкурентов — кто ранжится по вашим запросам
- Keyword gaps — запросы с высоким volume где вы не в top-10
- Отслеживание позиций — что выросло, что упало
- Backlinks — профиль обратных ссылок
- Технический аудит — meta теги, JSON-LD, внутренняя перелинковка, orphan pages

**AEO (Answer Engine Optimization — AI-чатботы):**
- Проверяет цитирует ли вас ChatGPT когда спрашивают про вашу нишу
- Проверяет Perplexity — возвращает конкретные URL которые он цитирует
- Проверяет Claude и Grok
- Можно проверять и на локальных моделях через Ollama (Qwen, Llama, Mistral)
- Всего 5 AI-провайдеров

**GEO (Google AI Overview):**
- Мониторит кого Google AI цитирует по вашим ключевым словам
- Показывает вашу позицию в органике рядом с AI Overview
- Если вас не цитируют — показывает кого цитируют вместо вас

**Плюс:**
- Генератор llms.txt — файл который помогает AI моделям понять ваш сайт
- Аналитика трафика через Plausible с разбивкой по AI-рефералам (chatgpt.com, perplexity.ai)
- IndexNow — мгновенная отправка URL в Bing и Yandex
- Bing Webmaster — важно потому что ChatGPT, Perplexity и Copilot используют Bing
- Полный Markdown-отчёт из 14 секций одной командой

### Как выглядит

```
$ searchstack ai

  ChatGPT:     3/5 cited
  Perplexity:  4/5 cited → с URL-ами
  Claude:      0/5 cited
  Grok:        2/5 cited
  Ollama:      1/5 cited

$ searchstack geo
  AI Overview: 9/12 keywords
  Цитирует нас: 1/9
  Вместо нас: monday.com (4x), asana.com (3x)

$ searchstack report
  14 sections → report_20260401.md
```

### Числа

- 22 команды
- 10 интеграций (5 cloud AI + локальные модели + GSC + DataForSEO + Plausible + Bing + IndexNow)
- Стоимость: ~$5/мес за полный мониторинг. Ahrefs стоит $99, Semrush $130 — и ни один не трекает AI
- Технический аудит (meta, schema, links, onpage) работает бесплатно без API ключей
- Можно поставить на сервер и запускать по cron

### Почему Bing важнее чем кажется

Факт который мало кто знает: 3 из 5 главных AI-поисковиков используют Bing:
- ChatGPT Search → Bing
- Perplexity → Bing
- Microsoft Copilot → Bing

Если вы не в Bing — вы невидимы для трёх AI-продуктов.

### Стек

Python, чистый CLI. Зависимости: google-auth, requests. Без тяжёлых фреймворков.

Установка одной командой:
```
pip install searchstack
```

GitHub: https://github.com/alexpospekhov/searchstack-aeo
PyPI: https://pypi.org/project/searchstack/

MIT лицензия. Пулл-реквесты welcome.
