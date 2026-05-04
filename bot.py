import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder

# 🔑 ТВОЙ ТОКЕН
BOT_TOKEN = "8281205863:AAFKmE4xaNkbYyTZDB5780qkQFDNfNA0cYM"

class QuizState(StatesGroup):
    answering = State()

QUESTIONS = [
    {"q": "Как часто ты употребляешь алкоголь?", "opts": [("Несколько раз в год", 0), ("1-2 раза в месяц", 1), ("1-2 раза в неделю", 2), ("Почти каждый день", 3)]},
    {"q": "Можешь остановиться после одного бокала?", "opts": [("Да легко", 0), ("Иногда сложно", 1), ("Редко получается", 2), ("Практически никогда", 3)]},
    {"q": "Пьёшь когда стрессово, тревожно или плохое настроение?", "opts": [("Нет", 0), ("Иногда", 1), ("Часто", 2), ("Почти всегда", 3)]},
    {"q": "Думаешь об алкоголе в течение дня — когда выпьешь, по какому поводу?", "opts": [("Нет", 0), ("Иногда мелькает мысль", 1), ("Довольно часто", 2), ("Практически постоянно", 3)]},
    {"q": "Бывает что выпиваешь больше чем планировал?", "opts": [("Нет", 0), ("Редко", 1), ("Часто", 2), ("Почти всегда", 3)]},
    {"q": "Пробовал сократить или бросить — не получилось?", "opts": [("Не пробовал", 0), ("Пробовал, получилось", 0), ("Пробовал, сложно", 2), ("Пробовал несколько раз, каждый раз возвращался", 3)]},
    {"q": "Как чувствуешь себя на следующий день после употребления?", "opts": [("Нормально", 0), ("Лёгкое недомогание", 1), ("Плохо, нужно время на восстановление", 2), ("Очень плохо, иногда похмеляюсь", 3)]},
    {"q": "Влияет ли алкоголь на работу, семью или здоровье?", "opts": [("Нет", 0), ("Незначительно", 1), ("Заметно влияет", 2), ("Серьёзно влияет", 3)]},
    {"q": "Используешь алкоголь чтобы расслабиться или переключиться?", "opts": [("Нет", 0), ("Иногда", 1), ("Регулярно", 2), ("Это основной способ расслабиться", 3)]},
    {"q": "Бывают провалы в памяти после употребления?", "opts": [("Никогда", 0), ("Очень редко", 1), ("Иногда", 2), ("Часто", 3)]},
    {"q": "Близкие люди говорили что ты пьёшь много?", "opts": [("Нет", 0), ("Намекали", 1), ("Говорили прямо", 2), ("Это серьёзная тема в семье", 3)]},
    {"q": "Чувствуешь вину или стыд после употребления?", "opts": [("Никогда", 0), ("Иногда", 1), ("Часто", 2), ("Почти всегда", 3)]}
]

def get_result_text(score: int) -> str:
    if score <= 8:
        return " 0-8 баллов — Всё под контролем\nПризнаков зависимости нет. Алкоголь присутствует в жизни умеренно и не влияет на качество жизни. Просто продолжай наблюдать за собой."
    elif score <= 18:
        return "🟡 9-18 баллов — Есть риски\nНекоторые паттерны поведения говорят о том что стоит обратить внимание. Зависимости пока нет — но она формируется незаметно. Хорошее время чтобы задуматься и пересмотреть привычки."
    else:
        return " 19-36 баллов — Высокий риск\nКартина говорит о сформировавшейся зависимости. Это не приговор — но это сигнал что пора действовать. Первый шаг — честно признать это себе. Именно с этого начинают все кто смог изменить свою жизнь."

dp = Dispatcher(storage=MemoryStorage())

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="🚀 Пройти тест", callback_data="start_quiz")
    
    await message.answer(
        "👋 **Привет! Это тест на выявление рисков употребления алкоголя.**\n\n"
        "Тест основан на реальном инструменте — называется AUDIT (Alcohol Use Disorders Identification Test). "
        "Это стандартный скрининг ВОЗ, который используют врачи по всему миру.\n\n"
        "Он состоит из 12 вопросов. Отвечай честно, никто не увидит твои ответы.\n\n"
        "Нажми кнопку ниже, чтобы начать:",
        reply_markup=kb.as_markup(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "start_quiz")
async def begin_quiz(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(current_q=0, score=0)
    await callback.message.delete()
    await send_question(callback.message, state)

async def send_question(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if data["current_q"] >= len(QUESTIONS):
        await finish_quiz(message, state)
        return

    q_data = QUESTIONS[data["current_q"]]
    kb = InlineKeyboardBuilder()
    for text, score in q_data["opts"]:
        kb.button(text=text, callback_data=str(score))
    kb.adjust(1)

    await message.answer(f" {q_data['q']}", reply_markup=kb.as_markup())
    await state.set_state(QuizState.answering)

@dp.callback_query(QuizState.answering, F.data.isdigit())
async def handle_answer(callback: types.CallbackQuery, state: FSMContext):
    score = int(callback.data)
    data = await state.get_data()
    data["score"] += score
    data["current_q"] += 1
    await state.update_data(**data)
    await callback.answer()
    await send_question(callback.message, state)

async def finish_quiz(message: types.Message, state: FSMContext):
    data = await state.get_data()
    result = get_result_text(data["score"])
    await message.answer(f"✅ Тест завершён!\n\n📊 Твой результат: {data['score']} из 36 баллов.\n\n{result}")
    await state.clear()

async def main():
    bot = Bot(token=BOT_TOKEN)
    await bot.delete_webhook(drop_pending_updates=True)
    print("🤖 Бот запущен с приветствием!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())