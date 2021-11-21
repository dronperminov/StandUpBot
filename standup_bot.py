import datetime
import pytz
from collections import defaultdict
import daemon
import lockfile
from telegram import Update
from telegram.ext import Updater, CallbackContext, CommandHandler


class StandUpBot:
    def __init__(self, token: str):
        self.users = defaultdict(set)
        self.chat_ids = set()
        self.updater = Updater(token=token, use_context=True)
        self.dispatcher = self.updater.dispatcher
        self.job_queue = self.updater.job_queue

        self.dispatcher.add_handler(CommandHandler('start', self.start))
        self.dispatcher.add_handler(CommandHandler('stop', self.stop))

        self.period = datetime.time(hour=18, minute=0, second=0, tzinfo=pytz.timezone('Europe/Moscow')),
        self.job_queue.run_daily(self.standup, days=(0, 1, 2, 3, 4), time=self.period)
        self.updater.start_polling()

    def start(self, update: Update, context: CallbackContext):
        chat_id = update.effective_chat.id
        username = update.message.from_user.username

        if username in self.users[chat_id]:
            message = f"@{username} уже находится в стендап списке"
        else:
            message = f"@{username} добавлен в стендап список"

        self.chat_ids.add(chat_id)
        self.users[chat_id].add(username)
        context.bot.send_message(chat_id=chat_id, text=message)

    def stop(self, update: Update, context: CallbackContext):
        chat_id = update.effective_chat.id
        username = update.message.from_user.username

        if username in self.users[chat_id]:
            self.users[chat_id].remove(username)
            message = f"@{username} удалён из стендап списка"
        else:
            message = f"@{username} отсутствует в стендап списке"

        context.bot.send_message(chat_id=chat_id, text=message)

    def standup(self, context: CallbackContext):
        for chat_id in self.chat_ids:
            if not self.users[chat_id]:
                continue

            message = '#стендап\n' + ' '.join(f'@{user}' for user in self.users[chat_id])
            context.bot.send_message(chat_id=chat_id, text=message)


def main():
    with daemon.DaemonContext():
        bot = StandUpBot('token')


if __name__ == '__main__':
    main()
