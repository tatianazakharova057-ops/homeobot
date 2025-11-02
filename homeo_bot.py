"""
Телеграм-бот для гомеопатических консультаций с использованием Claude API
"""

import os
import anthropic
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Получаем ключи из переменных окружения
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Инициализация Claude клиента
claude_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# Системный промпт для специализации на гомеопатии
SYSTEM_PROMPT = """Ты - опытный помощник по классической гомеопатии. 

Твои задачи:
1. Помогать подбирать гомеопатические препараты по описанным симптомам
2. Предоставлять информацию о ключевых характеристиках препаратов
3. Описывать модальности (улучшение/ухудшение состояния)
4. Указывать на характерные ментальные и физические симптомы

Важные принципы:
- Всегда рекомендуй консультацию с квалифицированным гомеопатом для точного назначения
- Базируйся на классической гомеопатической materia medica
- Указывай альтернативные препараты, если они подходят
- Будь конкретным и информативным
- Отвечай на русском языке

Никогда не ставь диагнозы и не заменяй медицинскую консультацию."""


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Приветственное сообщение при команде /start"""
    welcome_text = """
👋 Привет! Я бот-помощник по классической гомеопатии.

Я могу помочь тебе:
- Подобрать препарат по симптомам
- Узнать характеристики гомеопатических средств
- Получить информацию о модальностях

📝 Просто опиши симптомы, и я постараюсь помочь.

⚠️ Важно: Я не заменяю консультацию гомеопата! 
Для точного назначения обратись к специалисту.

Доступные команды:
/start - это сообщение
/help - помощь
/clear - очистить историю беседы
    """
    await update.message.reply_text(welcome_text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Помощь по использованию бота"""
    help_text = """
📚 Как пользоваться ботом:

1️⃣ Опиши симптомы максимально подробно:
   - Физические проявления
   - Эмоциональное состояние
   - Время ухудшения/улучшения
   - Пищевые пристрастия
   - Особенности характера

2️⃣ Примеры запросов:
   • "Головная боль справа, хуже от движения"
   • "Ребенок капризный, понос после сна в 16:00"
   • "Кашель сухой ночью, жажда холодной воды"

3️⃣ Можешь задавать уточняющие вопросы о препаратах

💡 Совет: чем детальнее описание, тем точнее подбор препарата!
    """
    await update.message.reply_text(help_text)


async def clear_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Очистка истории разговора"""
    if 'conversation_history' in context.user_data:
        context.user_data['conversation_history'] = []
    await update.message.reply_text("✅ История беседы очищена. Можешь начать новый запрос.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка сообщений пользователя"""
    user_message = update.message.text
    
    # Отправляем индикатор набора текста
    await update.message.chat.send_action(action="typing")
    
    try:
        # Инициализация истории беседы для пользователя
        if 'conversation_history' not in context.user_data:
            context.user_data['conversation_history'] = []
        
        # Добавляем сообщение пользователя в историю
        context.user_data['conversation_history'].append({
            "role": "user",
            "content": user_message
        })
        
        # Ограничиваем историю последними 10 сообщениями
        if len(context.user_data['conversation_history']) > 10:
            context.user_data['conversation_history'] = context.user_data['conversation_history'][-10:]
        
        # Запрос к Claude API
        response = claude_client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            messages=context.user_data['conversation_history']
        )
        
        # Получаем ответ от Claude
        assistant_message = response.content[0].text
        
        # Добавляем ответ в историю
        context.user_data['conversation_history'].append({
            "role": "assistant",
            "content": assistant_message
        })
        
        # Отправляем ответ пользователю
        await update.message.reply_text(assistant_message)
        
    except anthropic.APIError as e:
        error_message = f"❌ Ошибка API: {str(e)}\n\nПопробуй позже."
        await update.message.reply_text(error_message)
        
    except Exception as e:
        error_message = f"❌ Произошла ошибка: {str(e)}\n\nПопробуй еще раз."
        await update.message.reply_text(error_message)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    print(f"Ошибка: {context.error}")


def main():
    """Запуск бота"""
    # Создаем приложение
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("clear", clear_history))
    
    # Регистрируем обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Регистрируем обработчик ошибок
    application.add_error_handler(error_handler)
    
    # Запускаем бота
    print("🤖 Бот запущен и готов к работе!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
