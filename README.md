Climate Intelligence: Heatwave Monitoring, Prediction, and Early Warning
A web-based climate monitoring dashboard built with Python Flask,
PostgreSQL, HTML, and CSS. The project stores weather
observations and presents temperature analytics, heatwave events,
alerts, and forecast records through a browser-based interface.
GitHub Repository:
https://github.com/abdullahmujawar10/CLimate_Heatwave
Project Overview
Heatwaves can pose risks to public health, infrastructure, and the
environment. This project provides a central dashboard for viewing
weather-station readings and reviewing recorded heatwave events, alerts,
and forecast data.
The application connects a Flask web server to a PostgreSQL database.
Users can browse weather observations, add new readings, edit existing
readings, and view climate information in one place.
Features
- Dashboard overview --- counts of weather stations, sensor
  readings, heatwave events, and alerts.
- Temperature analytics --- highest, lowest, and average recorded
  temperatures.
- Temperature graph --- compares daily maximum and minimum
  recorded temperatures, with labels showing the weather station and
  date.
- Weather data management --- view, search, and filter sensor
  readings.
- Add readings --- save a new observation for a weather station.
- Edit and delete readings --- maintain existing sensor records.
- Heatwave events --- view event dates, maximum temperatures,
  severity, and descriptions.
- Alerts --- view stored alert levels, dates, times, and messages.
- Forecasts --- view forecast records, including predicted
  temperature, humidity, and heatwave probability.
Note: Forecasts and alerts displayed by the application are
records stored in the database. Do not describe the system as
generating live predictions or sending real-world emergency alerts
unless those capabilities are implemented and tested separately.

Technology Stack
- Frontend: HTML, CSS, Chart.js
- Backend: Python, Flask
- Database: PostgreSQL
- Database connector: psycopg2-binary
Project Structure
CLimate_Heatwave/
├── app.py
├── templates/
│   ├── index.html
│   ├── weather.html
│   ├── add_weather.html
│   ├── edit_weather.html
│   ├── heatwaves.html
│   ├── alerts.html
│   └── forecasts.html
└── static/
    └── style.css
Your repository may contain additional templates or files as features
are added.
Database
The application connects to a PostgreSQL database named
climate_heatwave_db.
The main tables used by the dashboard include:
- Region --- region details.
- WeatherStation --- weather-station information and its region.
- SensorReading --- date, time, temperature, humidity, wind speed,
  rainfall, and pressure readings.
- HeatwaveEvent --- recorded heatwave events and severity.
- Alert --- alert information associated with events.
- Forecast --- stored forecast values.
- PredictionModel --- prediction-model metadata.
The database must be created and populated with the required tables and
related records before all pages can display data. Ensure that the table
and column names in your database match the SQL queries in app.py.
Prerequisites
Install the following before running the project:
- Python 3
- PostgreSQL
- A PostgreSQL database named climate_heatwave_db
Installation and Setup
1. Clone the repository
git clone https://github.com/abdullahmujawar10/CLimate_Heatwave.git
cd CLimate_Heatwave
2. Create and activate a virtual environment (recommended)
On Windows Command Prompt:
python -m venv venv
venv\Scripts\activate
3. Install dependencies
pip install Flask psycopg2-binary
If a requirements.txt file is added to the repository, you can instead
install the listed dependencies with:
pip install -r requirements.txt
4. Configure PostgreSQL
Create or restore the database and make sure the project tables and data
are present.
In app.py, configure the database connection to match your local
PostgreSQL setup:
def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="climate_heatwave_db",
        user="postgres",
        password="YOUR_POSTGRES_PASSWORD",
        port="5432"
    )
Replace YOUR_POSTGRES_PASSWORD with your local PostgreSQL password.
Never commit your real password, API keys, or other secrets to
GitHub. For a public repository, use environment variables or a local
.env file excluded from version control.
5. Run the application
python app.py
Open this address in your browser:
http://127.0.0.1:5000
Keep the terminal open while using the application. Stop the local
server with Ctrl+C.
Main Pages
  Page                    Route                   Purpose
  Dashboard               /                     Summary cards,
                                                  temperature statistics,
                                                  graph, and recent
                                                  heatwave events
  Weather Data            /weather              Browse, search, filter,
                                                  add, edit, and delete
                                                  readings
  Add Weather Reading     /weather/add          Enter a new sensor
                                                  observation
  Heatwave Events         /heatwaves            Review recorded
                                                  heatwave events
  Alerts                  /alerts               Review stored alerts
  Forecasts               /forecasts            Review stored forecast
                                              records
How the Temperature Graph Works
The dashboard queries the SensorReading table and joins it with
WeatherStation. It groups readings by station and date, then
calculates the maximum and minimum recorded temperatures for each group.
Chart.js renders the returned values in the browser.
The graph reflects the records in the local database; its results depend
on the dates and stations available in that database.
Future Improvements
- Move database credentials into environment variables.
- Add a requirements.txt file and database setup/seed scripts.
- Add input validation and clearer error messages.
- Add pagination for large weather-reading tables.
- Improve graph filters so users can select a station and date range.
- Add automated tests.
- Implement and evaluate a documented forecasting model if actual
  prediction functionality is required.
- Add authentication and authorization before exposing the application
  publicly.
Security Notes
- Do not publish database passwords or other secrets.
- Use parameterized SQL queries when accepting user input.
- The Flask development server and debug=True are intended for local
  development, not production deployment.
- Back up your database before testing deletion or update features.
Academic Project
This project demonstrates how a relational database can be integrated
with a web application to organize weather data and display climate
analytics. It can be extended with additional data analysis and
forecasting functionality as future work.
