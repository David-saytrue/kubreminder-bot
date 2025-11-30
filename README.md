🤖 KubReminder — Telegram Bot for a Programming School

This is a Telegram bot designed to help teachers at the KubikRubik programming school manage their schedule and receive timely lesson reminders.

🚀 Features

📚 View Upcoming Lessons: Use /lessons to see the next few scheduled events.

📌 View Today's Lessons: Use /today to quickly check the schedule for the current day.

📝 Add New Lessons: Administrators can add new events using /add_lesson.

❌ Delete Lessons: Administrators can delete events using /delete_lesson.

🔔 Automatic Reminders: Sends notifications 30 minutes before a scheduled lesson.

⏰ Daily Digest: Sends a notification with all of today's lessons every day at 10:00 AM (Tbilisi time).

🛠 Setup and Launch

Requirements

Docker and Docker Compose (recommended for deployment)

Python 3.13+ (for local launch)

1. Clone the Repository

git clone <your-repo-url>
cd my_bot

2. Configure Environment Variables

Create a file named .env in the project root directory and fill in the required variables:

# Your bot's token from BotFather

TELEGRAM_BOT_TOKEN=your_bot_token

# The main chat ID for daily and general notifications (often the admin's personal chat)

CHAT_ID=your_main_chat_id

# The user ID of the administrator who can add/delete lessons

ADMIN_ID=your_admin_user_id

# Optional: Comma-separated list of group/channel IDs where the bot should send reminders (e.g., team chat)

# Example: ALLOWED_CHATS=-1001234567890,-1001987654321

ALLOWED_CHATS=

3. Launch via Docker (Recommended)

This method uses the provided Dockerfile and assumes you have a docker-compose.yml file configured.

# Build the image and run the container in detached mode

docker-compose up -d

4. Local Launch (Alternative)

For development or testing purposes:

# Create and activate a virtual environment

python -m venv my_env
source my_env/bin/activate # Linux/Mac

# or my_env\Scripts\activate # Windows

# Install dependencies (requires requirements.txt)

pip install -r requirements.txt

# Run the bot

python bot.py

📋 Bot Commands

/start — Greeting and bot information.

/lessons — Show the next upcoming lessons.

/today — Show all lessons scheduled for the current day.

/add_lesson YYYY-MM-DD HH:MM description — Add a lesson (Admin only).
Example: /add_lesson 2025-10-21 17:00 Prepare Python curriculum

/delete_lesson NUMBER — Delete a lesson by its list number (Admin only).

🔧 Configuration Details

Getting the Bot Token

Message @BotFather on Telegram.

Create a new bot using the /newbot command.

Copy the token provided and set it as TELEGRAM_BOT_TOKEN in .env.

Getting Your User ID (for CHAT_ID and ADMIN_ID)

Message @userinfobot.

Send it any message.

Copy your User ID and set it as CHAT_ID and ADMIN_ID in .env.

Adding the Bot to Groups and Channels

Add the bot to your target group/channel as an administrator.

Get the Group/Channel ID:

Add the bot @userinfobot to the group.

It will display the group ID (a negative number, e.g., -1001234567890).

Add the ID(s) to .env using a comma-separated list for ALLOWED_CHATS:

ALLOWED_CHATS=-1001234567890,-1001987654321

Important: The bot must be an administrator in the group/channel to send messages!

📁 Project Structure

my_bot/
├── bot.py # Main bot code and logic
├── requirements.txt # Python dependencies (python-telegram-bot, pytz)
├── Dockerfile # Docker image configuration (Python 3.13-slim)
├── docker-compose.yml # Docker Compose configuration (for easy launch)
├── .env # Environment variables (MUST NOT be committed!)
├── .gitignore # List of ignored files
└── data/ # Data volume for persistence
└── lessons.json # JSON file storing the lesson schedule

📝 Notes

The bot operates in the Asia/Tbilisi timezone. All times are interpreted relative to this timezone.

Lesson data is persisted in the lessons.json file inside the Docker volume (/app/data).

🤝 Support

If you encounter any issues, please check the following:

The correctness of your bot token.

The accuracy of CHAT_ID and ADMIN_ID.

The presence of all necessary environment variables in .env.

If Docker is running and the container is healthy.
