# run.py - Complete startup script
import threading
import time
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_environment():
    """Check if all required environment variables are set"""
    required_vars = [
        'TELEGRAM_BOT_TOKEN',
        'SUPABASE_URL',
        'SUPABASE_ANON_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease check your .env file and try again.")
        return False
    
    print("✅ All environment variables are set!")
    return True

def run_flask_app():
    """Run the Flask API server"""
    print("🚀 Starting Flask API server on http://localhost:5000...")
    try:
        # Import here to avoid issues with threading
        import app
        app.app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)
    except Exception as e:
        print(f"❌ Error starting Flask app: {e}")
        sys.exit(1)

def run_telegram_bot():
    """Run the Telegram bot"""
    print("🤖 Starting Telegram bot...")
    try:
        # Wait for Flask to start
        time.sleep(3)
        
        # Test API connection
        import requests
        try:
            response = requests.get('http://localhost:5000/api/health', timeout=5)
            if response.status_code == 200:
                print("✅ Flask API is running and accessible")
            else:
                print("⚠️ Flask API is running but returned unexpected status")
        except requests.exceptions.RequestException:
            print("⚠️ Could not connect to Flask API, but continuing with bot startup...")
        
        # Start Telegram bot
        from telegram_bot import main
        main()
    except Exception as e:
        print(f"❌ Error starting Telegram bot: {e}")
        sys.exit(1)

def main():
    """Main function to start both services"""
    print("🌟 Starting Disaster Management System...")
    print("=" * 50)
    
    # Check environment variables
    if not check_environment():
        return
    
    # Create and start threads
    flask_thread = threading.Thread(target=run_flask_app, daemon=True)
    bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
    
    try:
        # Start Flask API
        flask_thread.start()
        print("✅ Flask API thread started")
        
        # Start Telegram bot
        bot_thread.start()
        print("✅ Telegram bot thread started")
        
        print("\n🎉 Both services are starting up!")
        print("📝 Flask API: http://localhost:5000")
        print("🤖 Telegram Bot: Check your bot in Telegram")
        print("\nPress Ctrl+C to stop both services")
        
        # Keep main thread alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down services...")
        print("👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()