# Suraksha Setu Bot

A comprehensive system for reporting and managing disaster events through a Telegram bot and a Flask-based API, with data storage handled by Supabase.

## Features

*   **Telegram Bot Interface**: Allows users to report disasters, check the status of their reports, and trigger emergency alerts.
*   **Flask API Backend**: Handles incoming requests from the Telegram bot and potentially other clients, processes data, and interacts with the database.
*   **Supabase Integration**: Utilizes Supabase for robust and scalable data storage, including disaster reports, user information, and emergency alert logs.
*   **Comprehensive Reporting**: Users can provide details such_as disaster type, severity, location (latitude/longitude), description, and photos.
*   **Report Management**: Enables creation, retrieval (all reports, by user, by ID), status updates, and filtering of disaster reports.
*   **Emergency Alert System**: Automatically triggers alerts for reports marked with 'Critical' severity.
*   **Dashboard Statistics**: An API endpoint provides key statistics about the reported disasters (e.g., total reports, pending reports, types of disasters).
*   **Location-Based Queries**: Supports finding reports near a specific geographical location (though the current implementation is basic and can be improved).
*   **Environment-Based Configuration**: Uses a `.env` file for easy configuration of essential parameters like API keys and database URLs.
*   **Concurrent Operation**: Runs the Flask API and Telegram bot simultaneously using threading.

## Project Structure

```
.
├── .gitignore          # Specifies intentionally untracked files that Git should ignore
├── app.py              # Flask application: Defines API endpoints and handles HTTP requests
├── requirements.txt    # Lists Python dependencies for the project
├── run.py              # Startup script: Runs the Flask API and Telegram bot concurrently
├── supabase_client.py  # Supabase client: Manages interactions with the Supabase database
├── telegram_bot.py     # Telegram bot: Contains the logic for bot commands and user interactions
└── .env.example        # Example file for environment variables (copy to .env and fill in values)
```

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Raxy777/ss-bot.git
    cd ss-bot
    ```

2.  **Create and activate a Python virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up Supabase:**
    *   Go to [Supabase](https://supabase.com/) and create a new project.
    *   Inside your project, go to the SQL Editor and create the necessary tables. You'll likely need:
        *   `disaster_reports`: For storing disaster reports. Columns might include `id` (TEXT, primary key), `user_id` (TEXT), `username` (TEXT), `disaster_type` (TEXT), `severity` (TEXT), `latitude` (FLOAT), `longitude` (FLOAT), `description` (TEXT), `photos` (JSONB), `status` (TEXT, e.g., 'Pending', 'In Progress', 'Resolved'), `source` (TEXT), `created_at` (TIMESTAMPTZ), `updated_at` (TIMESTAMPTZ).
        *   `emergency_alerts`: For logging critical alerts. Columns might include `id` (UUID, primary key), `report_id` (TEXT, foreign key referencing `disaster_reports.id`), `alert_type` (TEXT), `severity` (TEXT), `location` (TEXT), `disaster_type` (TEXT), `description` (TEXT), `status` (TEXT), `created_at` (TIMESTAMPTZ).
        *   *Note: Adjust column names and types based on `supabase_client.py`.*
    *   In your Supabase project settings, find the **API** section to get your Project URL and the `anon` public key.

5.  **Set up Telegram Bot:**
    *   Open Telegram and search for "BotFather".
    *   Send `/newbot` command to BotFather and follow the instructions to create a new bot.
    *   BotFather will give you an **HTTP API token**. Keep this token secure.

6.  **Configure environment variables:**
    *   Create a `.env` file in the root of the project by copying `.env.example`:
        ```bash
        cp .env.example .env
        ```
    *   Open the `.env` file and fill in the following variables:
        ```env
        TELEGRAM_BOT_TOKEN="YOUR_TELEGRAM_BOT_TOKEN"
        SUPABASE_URL="YOUR_SUPABASE_PROJECT_URL"
        SUPABASE_ANON_KEY="YOUR_SUPABASE_ANON_KEY"
        BACKEND_API_URL="http://localhost:5000/api" # Default if running locally
        ```
        Replace the placeholder values with your actual credentials.

## Running the Application

Once you have completed the setup and installation steps:

1.  **Ensure your virtual environment is activated:**
    ```bash
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

2.  **Run the `run.py` script:**
    ```bash
    python run.py
    ```
    This script will:
    *   Check if all required environment variables are set.
    *   Start the Flask API server (typically on `http://localhost:5000`).
    *   Start the Telegram bot.

3.  **Interact with the System:**
    *   The Flask API will be accessible at the `BACKEND_API_URL` specified in your `.env` file (e.g., `http://localhost:5000/api`).
    *   Open Telegram and find the bot you created. You can start interacting with it using the commands like `/start`.

To stop both services, press `Ctrl+C` in the terminal where `run.py` is executing.

## API Endpoints

The Flask API provides the following endpoints. All endpoints are prefixed with `/api`.

*   **`POST /reports`**: Creates a new disaster report.
    *   **Request Body**: JSON object with report details (e.g., `user_id`, `disaster_type`, `severity`, `latitude`, `longitude`, `description`, `photos`).
    *   **Response**: JSON object with the created report data or an error message.

*   **`GET /reports/user/<user_id>`**: Retrieves reports for a specific user.
    *   **Path Parameter**: `user_id` (string).
    *   **Query Parameter**: `limit` (integer, optional, default: 10) - Max number of reports to return.
    *   **Response**: JSON array of report objects or an error message.

*   **`GET /reports/<report_id>`**: Retrieves a specific report by its ID.
    *   **Path Parameter**: `report_id` (string).
    *   **Response**: JSON object of the report or an error message if not found.

*   **`PUT /reports/<report_id>/status`**: Updates the status of a specific report.
    *   **Path Parameter**: `report_id` (string).
    *   **Request Body**: JSON object with `status` (string, e.g., 'Pending', 'In Progress', 'Resolved', 'Cancelled').
    *   **Response**: JSON object with the updated report data or an error message.

*   **`GET /reports`**: Retrieves all reports with optional filters.
    *   **Query Parameters (optional)**:
        *   `severity` (string)
        *   `disaster_type` (string)
        *   `status` (string)
        *   `limit` (integer, optional, default: 50)
    *   **Response**: JSON object containing a list of reports and the count.

*   **`GET /reports/nearby`**: Retrieves reports near a specific location.
    *   **Query Parameters**:
        *   `lat` (float, required): Latitude of the center point.
        *   `lng` (float, required): Longitude of the center point.
        *   `radius` (float, optional, default: 10): Radius in kilometers.
    *   **Response**: JSON object containing a list of nearby reports, count, center coordinates, and radius.

*   **`GET /dashboard/stats`**: Retrieves various statistics for a dashboard.
    *   **Response**: JSON object with statistics like total reports, reports by status, reports by severity, disaster type breakdown, and recent reports.

*   **`GET /health`**: Health check endpoint for the API.
    *   **Response**: JSON object indicating the service status.

Error responses typically include a JSON object with an `error` key.

## Telegram Bot Commands

Interact with the Disaster Management System bot on Telegram using the following commands and interface elements:

*   **`/start`**: Initializes the bot and displays a welcome message with main interaction buttons.
*   **`🚨 Report Disaster` (Button) or `/report` (Command)**: Initiates the process of reporting a new disaster. The bot will guide you through steps to select:
    *   Disaster type (e.g., Earthquake, Flood, Fire)
    *   Severity level (Low, Medium, High, Critical)
    *   Location (shared via Telegram's location feature)
    *   Description (text input, optional)
    *   Photos (image uploads, optional)
*   **`📊 My Reports` (Button) or `/status` (Command)**: Shows a list of your recently submitted reports and their current status.
*   **`ℹ️ Help` (Button) or `/help` (Command)**: Displays help information, including instructions on how to report disasters and emergency contact details.
*   **`🆘 Emergency` (Button) or `/emergency` (Command)**: Initiates a quick emergency report. This prioritizes location sharing and marks the report as 'Critical'.

The bot uses a combination of text commands and interactive buttons (inline and reply keyboards) to guide users through the reporting process.

## Contributing

Contributions are welcome! If you have suggestions for improvements or want to contribute code, please follow these general steps:

1.  **Fork the Project.**
2.  **Create your Feature Branch:**
    ```bash
    git checkout -b feature/AmazingFeature
    ```
3.  **Commit your Changes:**
    ```bash
    git commit -m 'Add some AmazingFeature'
    ```
4.  **Push to the Branch:**
    ```bash
    git push origin feature/AmazingFeature
    ```
5.  **Open a Pull Request.**

Please ensure your code adheres to the project's coding standards and includes tests where applicable.
