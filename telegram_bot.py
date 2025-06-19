import os
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import requests
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
BACKEND_API_URL = os.getenv('BACKEND_API_URL', 'http://localhost:5000/api')

# Disaster types
DISASTER_TYPES = [
    'Earthquake', 'Flood', 'Fire', 'Landslide', 'Cyclone', 
    'Accident', 'Medical Emergency', 'Other'
]

# Severity levels
SEVERITY_LEVELS = ['Low', 'Medium', 'High', 'Critical']

class DisasterReportBot:
    def __init__(self):
        self.user_sessions = {}
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start command handler"""
        user = update.effective_user
        welcome_message = f"""
🚨 **Disaster Management System Bot** 🚨

Hello {user.first_name}! I'm here to help you report disasters and emergencies.

**Available Commands:**
/report - Report a new disaster
/status - Check your recent reports
/help - Get help and instructions
/emergency - Quick emergency report

Stay safe! 🙏
        """
        
        keyboard = [
            [KeyboardButton("🚨 Report Disaster")],
            [KeyboardButton("📊 My Reports"), KeyboardButton("ℹ️ Help")],
            [KeyboardButton("🆘 Emergency")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode='Markdown')

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Help command handler"""
        help_text = """
📋 **How to Report a Disaster:**

1. Use /report or click "🚨 Report Disaster"
2. Select disaster type
3. Choose severity level
4. Share your location
5. Add description and photos (optional)
6. Submit report

**Emergency Reporting:**
- Use /emergency for critical situations
- Your location will be immediately requested
- Report will be marked as high priority

**Important:**
- Always ensure your safety first
- Provide accurate information
- Include photos if safe to do so
- Emergency services will be notified for critical reports

Need immediate help? Contact emergency services: 112
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def start_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start disaster reporting process"""
        user_id = update.effective_user.id
        
        # Initialize user session
        self.user_sessions[user_id] = {
            'step': 'disaster_type',
            'report_data': {
                'user_id': user_id,
                'username': update.effective_user.username,
                'timestamp': datetime.now().isoformat()
            }
        }
        
        # Create inline keyboard for disaster types
        keyboard = []
        for i in range(0, len(DISASTER_TYPES), 2):
            row = []
            row.append(InlineKeyboardButton(DISASTER_TYPES[i], callback_data=f"type_{DISASTER_TYPES[i]}"))
            if i + 1 < len(DISASTER_TYPES):
                row.append(InlineKeyboardButton(DISASTER_TYPES[i + 1], callback_data=f"type_{DISASTER_TYPES[i + 1]}"))
            keyboard.append(row)
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("🔍 What type of disaster are you reporting?", reply_markup=reply_markup)

    async def emergency_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Quick emergency report"""
        user_id = update.effective_user.id
        
        self.user_sessions[user_id] = {
            'step': 'emergency_location',
            'report_data': {
                'user_id': user_id,
                'username': update.effective_user.username,
                'disaster_type': 'Emergency',
                'severity': 'Critical',
                'timestamp': datetime.now().isoformat()
            }
        }
        
        keyboard = [[KeyboardButton("📍 Share Location", request_location=True)]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        
        await update.message.reply_text(
            "🆘 **EMERGENCY REPORT**\n\nPlease share your current location immediately!",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline keyboard button presses"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        data = query.data
        
        if user_id not in self.user_sessions:
            await query.message.reply_text("❌ Session expired. Please start a new report with /report")
            return
        
        session = self.user_sessions[user_id]
        
        if data.startswith('type_'):
            # Disaster type selection
            disaster_type = data.replace('type_', '')
            session['report_data']['disaster_type'] = disaster_type
            session['step'] = 'severity'
            
            # Create severity keyboard
            keyboard = []
            for i in range(0, len(SEVERITY_LEVELS), 2):
                row = []
                row.append(InlineKeyboardButton(f"{SEVERITY_LEVELS[i]}", callback_data=f"severity_{SEVERITY_LEVELS[i]}"))
                if i + 1 < len(SEVERITY_LEVELS):
                    row.append(InlineKeyboardButton(f"{SEVERITY_LEVELS[i + 1]}", callback_data=f"severity_{SEVERITY_LEVELS[i + 1]}"))
                keyboard.append(row)
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                f"✅ Disaster Type: **{disaster_type}**\n\n📊 What is the severity level?",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        
        elif data.startswith('severity_'):
            # Severity selection
            severity = data.replace('severity_', '')
            session['report_data']['severity'] = severity
            session['step'] = 'location'
            
            keyboard = [[KeyboardButton("📍 Share Location", request_location=True)]]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
            
            await query.edit_message_text(
                f"✅ Disaster Type: **{session['report_data']['disaster_type']}**\n"
                f"✅ Severity: **{severity}**\n\n"
                f"📍 Please share your location:",
                parse_mode='Markdown'
            )
            await query.message.reply_text("Click the button below to share your location:", reply_markup=reply_markup)

    async def handle_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle location sharing"""
        user_id = update.effective_user.id
        
        if user_id not in self.user_sessions:
            await update.message.reply_text("❌ Session expired. Please start a new report with /report")
            return
        
        session = self.user_sessions[user_id]
        location = update.message.location
        
        session['report_data']['latitude'] = location.latitude
        session['report_data']['longitude'] = location.longitude
        session['step'] = 'description'
        
        # Remove location keyboard
        keyboard = [
            [KeyboardButton("Skip Description")],
            [KeyboardButton("🚨 Report Disaster"), KeyboardButton("Cancel")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        if session['step'] == 'emergency_location':
            # For emergency reports, submit immediately
            await self.submit_report(update, context, emergency=True)
        else:
            await update.message.reply_text(
                "✅ Location received!\n\n"
                "📝 Please provide a description of the situation (or click 'Skip Description'):",
                reply_markup=reply_markup
            )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages"""
        user_id = update.effective_user.id
        text = update.message.text
        
        # Handle button presses
        if text == "🚨 Report Disaster":
            await self.start_report(update, context)
            return
        elif text == "🆘 Emergency":
            await self.emergency_report(update, context)
            return
        elif text == "ℹ️ Help":
            await self.help_command(update, context)
            return
        elif text == "📊 My Reports":
            await self.show_user_reports(update, context)
            return
        
        if user_id not in self.user_sessions:
            await update.message.reply_text(
                "👋 Hi! Use /start to begin or /report to report a disaster."
            )
            return
        
        session = self.user_sessions[user_id]
        
        if session['step'] == 'description':
            if text == "Skip Description":
                session['report_data']['description'] = "No description provided"
            else:
                session['report_data']['description'] = text
            
            session['step'] = 'photos'
            
            keyboard = [
                [KeyboardButton("Skip Photos")],
                [KeyboardButton("Submit Report")]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            
            await update.message.reply_text(
                "📸 You can now send photos (optional) or click 'Submit Report' to finish:",
                reply_markup=reply_markup
            )
        
        elif text == "Submit Report":
            await self.submit_report(update, context)

    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle photo uploads"""
        user_id = update.effective_user.id
        
        if user_id not in self.user_sessions:
            return
        
        session = self.user_sessions[user_id]
        
        if session['step'] == 'photos':
            # Get the largest photo
            photo = update.message.photo[-1]
            file = await context.bot.get_file(photo.file_id)
            
            # Store photo info (in real implementation, you'd upload to your server)
            if 'photos' not in session['report_data']:
                session['report_data']['photos'] = []
            
            session['report_data']['photos'].append({
                'file_id': photo.file_id,
                'file_path': file.file_path
            })
            
            await update.message.reply_text(
                f"✅ Photo received! ({len(session['report_data']['photos'])} total)\n"
                "Send more photos or click 'Submit Report' to finish."
            )

    async def submit_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE, emergency=False):
        """Submit the disaster report to backend"""
        user_id = update.effective_user.id
        
        if user_id not in self.user_sessions:
            return
        
        session = self.user_sessions[user_id]
        report_data = session['report_data']
        
        try:
            # Send to your backend API
            response = requests.post(
                f"{BACKEND_API_URL}/reports",
                json=report_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 201:
                report_id = response.json().get('id', 'Unknown')
                
                # Remove keyboard
                keyboard = [
                    [KeyboardButton("🚨 Report Disaster")],
                    [KeyboardButton("📊 My Reports"), KeyboardButton("ℹ️ Help")]
                ]
                reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                
                success_message = f"""
✅ **Report Submitted Successfully!**

🆔 Report ID: `{report_id}`
🏷️ Type: {report_data.get('disaster_type', 'N/A')}
📊 Severity: {report_data.get('severity', 'N/A')}
📍 Location: Received
⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{"🚨 Emergency services have been notified!" if emergency or report_data.get('severity') == 'Critical' else "📋 Your report is being processed."}

Thank you for helping keep the community safe! 🙏
                """
                
                await update.message.reply_text(
                    success_message,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                
            else:
                raise Exception(f"API Error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error submitting report: {e}")
            await update.message.reply_text(
                "❌ Error submitting report. Please try again or contact support.\n"
                f"Error: {str(e)}"
            )
        
        finally:
            # Clear user session
            if user_id in self.user_sessions:
                del self.user_sessions[user_id]

    async def show_user_reports(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user's recent reports"""
        user_id = update.effective_user.id
        
        try:
            response = requests.get(f"{BACKEND_API_URL}/reports/user/{user_id}")
            
            if response.status_code == 200:
                reports = response.json()
                
                if not reports:
                    await update.message.reply_text("📭 You haven't submitted any reports yet.")
                    return
                
                message = "📊 **Your Recent Reports:**\n\n"
                
                for report in reports[:5]:  # Show last 5 reports
                    message += f"🆔 **{report.get('id', 'N/A')}**\n"
                    message += f"🏷️ {report.get('disaster_type', 'N/A')}\n"
                    message += f"📊 {report.get('severity', 'N/A')}\n"
                    message += f"📅 {report.get('timestamp', 'N/A')}\n"
                    message += f"📋 {report.get('status', 'Pending')}\n\n"
                
                await update.message.reply_text(message, parse_mode='Markdown')
                
            else:
                await update.message.reply_text("❌ Unable to fetch your reports. Please try again later.")
                
        except Exception as e:
            logger.error(f"Error fetching user reports: {e}")
            await update.message.reply_text("❌ Error fetching reports. Please try again later.")

def main():
    """Main function to run the bot"""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables")
        return
    
    # Create bot instance
    bot = DisasterReportBot()
    
    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("report", bot.start_report))
    application.add_handler(CommandHandler("emergency", bot.emergency_report))
    application.add_handler(CommandHandler("help", bot.help_command))
    application.add_handler(CommandHandler("status", bot.show_user_reports))
    
    application.add_handler(CallbackQueryHandler(bot.button_callback))
    application.add_handler(MessageHandler(filters.LOCATION, bot.handle_location))
    application.add_handler(MessageHandler(filters.PHOTO, bot.handle_photo))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    
    # Start the bot
    logger.info("Starting Telegram Bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()