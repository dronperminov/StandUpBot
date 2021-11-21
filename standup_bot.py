import datetime
import pytz
from collections import defaultdict
import holidays
import daemon
from telegram import Update, ParseMode
from telegram.ext import Updater, CallbackContext, CommandHandler


class StandUpBot:
    def __init__(self, token: str):
        self.users = defaultdict(set)
        self.is_enabled = defaultdict(bool)
        self.chat_ids = set()
        self.ru_holidays = holidays.Russia()

        self.days = (0, 1, 2, 3, 4)
        self.period = datetime.time(hour=18, minute=0, second=0, tzinfo=pytz.timezone('Europe/Moscow'))

        updater = Updater(token=token, use_context=True)
        dispatcher = updater.dispatcher
        job_queue = updater.job_queue

        dispatcher.add_handler(CommandHandler('help', self.help))
        dispatcher.add_handler(CommandHandler('add', self.add))
        dispatcher.add_handler(CommandHandler('remove', self.remove))
        dispatcher.add_handler(CommandHandler('info', self.info))
        dispatcher.add_handler(CommandHandler('enable', self.enable))
        dispatcher.add_handler(CommandHandler('disable', self.disable))

        job_queue.run_daily(self.standup, days=self.days, time=self.period)
        updater.start_polling()

    def help(self, update: Update, context: CallbackContext):
        commands = [
            '`/help` - вывести данное сообщение',
            '`/add` - добавить себя в список стендапа',
            '`/remove` - исключить себя из списка стендапа',
            '`/disable` - приостановить работу бота',
            '`/enable` - возобновить работу бота',
            '`/info` - вывести информацию о работе',
        ]

        message = 'Стендап бот поддерживает следующие команды:\n{}'.format('\n'.join(commands))
        context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode=ParseMode.MARKDOWN)

    def add(self, update: Update, context: CallbackContext):
        chat_id = update.effective_chat.id
        username = update.message.from_user.username

        if username in self.users[chat_id]:
            message = f"@{username} уже находится в стендап списке"
        else:
            message = f"@{username} добавлен в стендап список"

        if chat_id not in self.chat_ids:
            self.is_enabled[chat_id] = True

        self.chat_ids.add(chat_id)
        self.users[chat_id].add(username)
        context.bot.send_message(chat_id=chat_id, text=message)

    def remove(self, update: Update, context: CallbackContext):
        chat_id = update.effective_chat.id
        username = update.message.from_user.username

        if username in self.users[chat_id]:
            self.users[chat_id].remove(username)
            message = f"@{username} удалён из стендап списка"
        else:
            message = f"@{username} отсутствует в стендап списке"

        context.bot.send_message(chat_id=chat_id, text=message)

    def info(self, update: Update, context: CallbackContext):
        info = [
            f'<b>Статус</b>: {"активен" if self.is_enabled[update.effective_chat.id] else "неактивен"}',
            '<b>Время стендапа</b>: {:d}:{:02d}'.format(self.period.hour, self.period.minute),
            f'<b>Количество вызываемых участников</b>: {len(self.users[update.effective_chat.id])}',
        ]

        context.bot.send_message(chat_id=update.effective_chat.id, text='\n'.join(info), parse_mode=ParseMode.HTML)

    def enable(self, update: Update, context: CallbackContext):
        if self.is_enabled[update.effective_chat.id]:
            return

        self.is_enabled[update.effective_chat.id] = True
        context.bot.send_message(chat_id=update.effective_chat.id, text='Статус обновлён: бот активен')

    def disable(self, update: Update, context: CallbackContext):
        if not self.is_enabled[update.effective_chat.id]:
            return

        self.is_enabled[update.effective_chat.id] = False
        context.bot.send_message(chat_id=update.effective_chat.id, text='Статус обновлён: бот неактивен')

    def standup(self, context: CallbackContext):
        for chat_id in self.chat_ids:
            if not self.users[chat_id] or not self.is_enabled[chat_id]:
                continue

            if datetime.date.today() in self.ru_holidays:
                continue

            message = '#стендап\n' + ' '.join(f'@{user}' for user in self.users[chat_id])
            context.bot.send_message(chat_id=chat_id, text=message)


def main():
    with daemon.DaemonContext():
        bot = StandUpBot('token')


if __name__ == '__main__':
    main()
