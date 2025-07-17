from config import ADMIN_CHAT_ID

class RequestService:
    def __init__(self, db, bot):
        self.db = db
        self.bot = bot

    async def create_request(self, user_id, description, contact):
        if self.db.user_has_request(user_id):
            return False
        
        self.db.add_request(user_id, description, contact)

        message = (
            f"📬 *Новый запрос:* \n"
            f"👤 *User ID:* `{user_id}`\n"
            f"📦 *Описание:* {description}\n"
            f"📞 *Контакт:* {contact}"
        )

        await self.notify_admin(message)
        return True

    async def notify_admin(self, message):
        await self.bot.send_message(chat_id=ADMIN_CHAT_ID, text=message)