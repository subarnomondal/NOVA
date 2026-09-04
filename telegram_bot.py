import os
import sys
import yaml
import logging
from telegram import Update, BotCommand
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler, Application

# Create data directories
os.makedirs("userdata", exist_ok=True)
os.makedirs("userdata/config", exist_ok=True)

# Add project root to sys.path
root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from core.assistant import Clio

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def load_config():
    path = os.path.join("userdata", "config", "settings.yaml")
    if os.path.exists(path):
        with open(path, "r") as f:
            return yaml.safe_load(f)
    return {}

config = load_config()
bot_token = config.get("telegram", {}).get("bot_token", "")
allowed_users = config.get("telegram", {}).get("allowed_users", [])

if not bot_token or bot_token == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
    print("Error: Please set your telegram bot_token in userdata/config/settings.yaml")
    sys.exit(1)
    print("Error: Please set your telegram bot_token in userdata/config/settings.yaml")
    sys.exit(1)

# Initialize CLIO Assistant
print("Initializing CLIO...")
clio = Clio()
print("CLIO Initialized successfully!")

def is_authorized(update: Update) -> bool:
    if not allowed_users:
        return True # If no allowed users are set, assume open (or could change to False for strict)
    if not update.effective_user:
        return False
    
    # Telegram usernames can be None if the user hasn't set one
    username = update.effective_user.username
    if not username:
        return False
        
    return username in allowed_users

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat:
        return
        
    if not is_authorized(update):
        username = update.effective_user.username if update.effective_user else "Unknown"
        logging.warning(f"Unauthorized /start attempt from user: {username}")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, you are not authorized to use this bot.")
        return
        
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=f"Hello! I am {clio.name}, your Local Autonomous Responsive Agent. How can I help you today?"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat:
        return
    if not is_authorized(update):
        return
        
    help_text = (
        "🤖 *CLIO Bot Commands*\n\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/ping - Check if CLIO is online\n\n"
        "You can also just type any message and I will process it!"
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=help_text,
        parse_mode='Markdown'
    )

async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat:
        return
    if not is_authorized(update):
        return
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text="🏓 Pong! CLIO is online and ready."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text or not update.effective_chat:
        return
        
    if not is_authorized(update):
        username = update.effective_user.username if update.effective_user else "Unknown"
        logging.warning(f"Unauthorized access attempt from user: {username}")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, you are not authorized to use this bot.")
        return
        
    user_message = update.message.text
    chat_id = update.effective_chat.id
    
    # Optional: Send a 'typing' action
    await context.bot.send_chat_action(chat_id=chat_id, action='typing')
    
    # Process message via Clio
    try:
        result = clio.handle_input(user_message)
        
        response_text = "I'm sorry, I couldn't process that request."
        if isinstance(result, str):
            response_text = result
        elif isinstance(result, dict) and 'response' in result:
            response_text = result['response']
            
        await context.bot.send_message(chat_id=chat_id, text=response_text)
    except Exception as e:
        logging.error(f"Error handling message: {e}")
        await context.bot.send_message(chat_id=chat_id, text=f"An error occurred: {str(e)}")

async def post_init(application: Application) -> None:
    # Set the bot's command menu
    await application.bot.set_my_commands([
        BotCommand("start", "Start the bot"),
        BotCommand("help", "Show help message"),
        BotCommand("ping", "Check if CLIO is online"),
    ])

if __name__ == '__main__':
    application = ApplicationBuilder().token(bot_token).post_init(post_init).build()
    
    start_handler = CommandHandler('start', start)
    help_handler = CommandHandler('help', help_command)
    ping_handler = CommandHandler('ping', ping_command)
    message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
    
    application.add_handler(start_handler)
    application.add_handler(help_handler)
    application.add_handler(ping_handler)
    application.add_handler(message_handler)
    
    print("Starting Telegram Bot... Press Ctrl+C to stop.")
    application.run_polling()
