
from flask import Flask, render_template, request, redirect
import psycopg2

app = Flask(__name__)


# ==========================================
# DATABASE CONNECTION
# ==========================================

def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="climate_heatwave_db",
        user="postgres",
        password="maryam",
        port="5432"
    )


# ==========================================
# HELPER: FETCH LATEST READING PER STATION
# ==========================================

def get_latest_station_readings():
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT DISTINCT ON (w.station_id)
                w.station_id,
                w.station_name,
                r.region_name,
                w.latitude,
                w.longitude,
                s.reading_date,
                s.reading_time,
                s.temperature,
                s.humidity,
                s.wind_speed
            FROM WeatherStation w
            LEFT JOIN Region r
                ON w.region_id = r.region_id
            LEFT JOIN SensorReading s
                ON w.station_id = s.station_id
            ORDER BY
                w.station_id,
                s.reading_date DESC NULLS LAST,
                s.reading_time DESC NULLS LAST,
                s.reading_id DESC NULLS LAST;
        """)

        return cursor.fetchall()

    finally:
        cursor.close()
        conn.close()


# ==========================================
# HELPER: HEATWAVE RISK CLASSIFICATION
# ==========================================

def classify_heat_risk(temperature):
    """
    Demonstration thresholds only.
    These are not official meteorological warning criteria.
    """

    if temperature is None:
        return "Unknown"

    temperature = float(temperature)

    if temperature < 30:
        return "Low"
    elif temperature < 35:
        return "Moderate"
    elif temperature < 40:
        return "High"
    else:
        return "Extreme"


def get_risk_color(risk):
    colors = {
        "Low": "#22c55e",
        "Moderate": "#eab308",
        "High": "#f97316",
        "Extreme": "#ef4444",
        "Unknown": "#64748b"
    }

    return colors.get(risk, "#64748b")


# ==========================================
# DASHBOARD
# ==========================================

@app.route("/")
def dashboard():

    conn = get_db_connection()
    cursor = conn.cursor()

    # Count weather stations
    cursor.execute("""
        SELECT COUNT(*) FROM WeatherStation;
    """)
    station_count = cursor.fetchone()[0]

    # Count sensor readings
    cursor.execute("""
        SELECT COUNT(*) FROM SensorReading;
    """)
    reading_count = cursor.fetchone()[0]

    # Count heatwave events
    cursor.execute("""
        SELECT COUNT(*) FROM HeatwaveEvent;
    """)
    heatwave_count = cursor.fetchone()[0]

    # Count alerts
    cursor.execute("""
        SELECT COUNT(*) FROM Alert;
    """)
    alert_count = cursor.fetchone()[0]

    # Maximum, minimum and average recorded temperature
    cursor.execute("""
        SELECT
            MAX(temperature),
            MIN(temperature),
            ROUND(AVG(temperature), 2)
        FROM SensorReading;
    """)

    temperature_stats = cursor.fetchone()

    max_temperature = temperature_stats[0]
    min_temperature = temperature_stats[1]
    avg_temperature = temperature_stats[2]

    # Daily maximum and minimum temperatures by station and date
    cursor.execute("""
        SELECT
            w.station_name,
            s.reading_date,
            MAX(s.temperature),
            MIN(s.temperature)
        FROM SensorReading s
        JOIN WeatherStation w
            ON s.station_id = w.station_id
        GROUP BY w.station_name, s.reading_date
        ORDER BY s.reading_date DESC, w.station_name
        LIMIT 14;
    """)

    daily_rows = cursor.fetchall()

    # Display graph entries chronologically
    daily_rows.reverse()

    # Include station name and date in graph labels
    chart_labels = [
        f"{row[0]} - {row[1].strftime('%d %b %Y')}"
        for row in daily_rows
    ]

    chart_maximums = [
        float(row[2]) if row[2] is not None else None
        for row in daily_rows
    ]

    chart_minimums = [
        float(row[3]) if row[3] is not None else None
        for row in daily_rows
    ]

    # Get the five most recent heatwave events
    cursor.execute("""
        SELECT
            h.event_id,
            w.station_name,
            h.maximum_temperature,
            h.severity,
            h.start_date
        FROM HeatwaveEvent h
        JOIN WeatherStation w
            ON h.station_id = w.station_id
        ORDER BY h.start_date DESC, h.event_id DESC
        LIMIT 5;
    """)

    recent_heatwaves = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "index.html",
        station_count=station_count,
        reading_count=reading_count,
        heatwave_count=heatwave_count,
        alert_count=alert_count,
        max_temperature=max_temperature,
        min_temperature=min_temperature,
        avg_temperature=avg_temperature,
        chart_labels=chart_labels,
        chart_maximums=chart_maximums,
        chart_minimums=chart_minimums,
        recent_heatwaves=recent_heatwaves
    )


# ==========================================
# WEATHER DATA: SEARCH AND FILTER
# ==========================================

@app.route("/weather")
def weather():

    search = request.args.get("search", "")
    station = request.args.get("station", "")
    region = request.args.get("region", "")

    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            s.reading_id,
            w.station_name,
            r.region_name,
            s.temperature,
            s.humidity,
            s.wind_speed,
            s.reading_time
        FROM SensorReading s
        JOIN WeatherStation w
            ON s.station_id = w.station_id
        JOIN Region r
            ON w.region_id = r.region_id
        WHERE 1=1
    """

    parameters = []

    if search:
        query += " AND w.station_name ILIKE %s"
        parameters.append("%" + search + "%")

    if station:
        query += " AND w.station_id = %s"
        parameters.append(station)

    if region:
        query += " AND r.region_id = %s"
        parameters.append(region)

    query += " ORDER BY s.reading_id DESC;"

    cursor.execute(query, parameters)
    readings = cursor.fetchall()

    cursor.execute("""
        SELECT station_id, station_name
        FROM WeatherStation
        ORDER BY station_id;
    """)
    stations = cursor.fetchall()

    cursor.execute("""
        SELECT region_id, region_name
        FROM Region
        ORDER BY region_id;
    """)
    regions = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "weather.html",
        readings=readings,
        stations=stations,
        regions=regions,
        search=search,
        selected_station=station,
        selected_region=region
    )


# ==========================================
# ADD WEATHER READING
# ==========================================

@app.route("/weather/add", methods=["GET", "POST"])
def add_weather():

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == "GET":

        cursor.execute("""
            SELECT station_id, station_name
            FROM WeatherStation
            ORDER BY station_id;
        """)

        stations = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template(
            "add_weather.html",
            stations=stations
        )

    station_id = request.form["station_id"]
    reading_date = request.form["reading_date"]
    reading_time = request.form["reading_time"]
    temperature = request.form["temperature"]
    humidity = request.form["humidity"]
    wind_speed = request.form["wind_speed"]
    rainfall = request.form["rainfall"]
    pressure = request.form["pressure"]

    cursor.execute("""
        INSERT INTO SensorReading (
            station_id,
            reading_date,
            reading_time,
            temperature,
            humidity,
            wind_speed,
            rainfall,
            pressure
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
    """, (
        station_id,
        reading_date,
        reading_time,
        temperature,
        humidity,
        wind_speed,
        rainfall,
        pressure
    ))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect("/weather")


# ==========================================
# EDIT WEATHER READING
# ==========================================

@app.route(
    "/weather/edit/<int:reading_id>",
    methods=["GET", "POST"]
)
def edit_weather(reading_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == "GET":

        cursor.execute("""
            SELECT
                reading_id,
                station_id,
                reading_date,
                reading_time,
                temperature,
                humidity,
                wind_speed,
                rainfall,
                pressure
            FROM SensorReading
            WHERE reading_id = %s;
        """, (reading_id,))

        reading = cursor.fetchone()

        cursor.execute("""
            SELECT station_id, station_name
            FROM WeatherStation
            ORDER BY station_id;
        """)

        stations = cursor.fetchall()

        cursor.close()
        conn.close()

        if reading is None:
            return "Weather reading not found", 404

        return render_template(
            "edit_weather.html",
            reading=reading,
            stations=stations
        )

    station_id = request.form["station_id"]
    reading_date = request.form["reading_date"]
    reading_time = request.form["reading_time"]
    temperature = request.form["temperature"]
    humidity = request.form["humidity"]
    wind_speed = request.form["wind_speed"]
    rainfall = request.form["rainfall"]
    pressure = request.form["pressure"]

    cursor.execute("""
        UPDATE SensorReading
        SET
            station_id = %s,
            reading_date = %s,
            reading_time = %s,
            temperature = %s,
            humidity = %s,
            wind_speed = %s,
            rainfall = %s,
            pressure = %s
        WHERE reading_id = %s;
    """, (
        station_id,
        reading_date,
        reading_time,
        temperature,
        humidity,
        wind_speed,
        rainfall,
        pressure,
        reading_id
    ))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect("/weather")


# ==========================================
# DELETE WEATHER READING
# ==========================================

@app.route("/weather/delete/<int:reading_id>")
def delete_weather(reading_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM SensorReading
        WHERE reading_id = %s;
    """, (reading_id,))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect("/weather")


# ==========================================
# HEATWAVE EVENTS
# ==========================================

@app.route("/heatwaves")
def heatwaves():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            h.event_id,
            w.station_name,
            h.start_date,
            h.end_date,
            h.maximum_temperature,
            h.severity,
            h.description
        FROM HeatwaveEvent h
        JOIN WeatherStation w
            ON h.station_id = w.station_id
        ORDER BY h.event_id DESC;
    """)

    events = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "heatwaves.html",
        events=events
    )


# ==========================================
# ALERTS
# ==========================================

@app.route("/alerts")
def alerts():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            alert_id,
            event_id,
            alert_date,
            alert_time,
            alert_level,
            message
        FROM Alert
        ORDER BY alert_id DESC;
    """)

    alerts = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "alerts.html",
        alerts=alerts
    )


# ==========================================
# FORECASTS
# ==========================================

@app.route("/forecasts")
def forecasts():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            f.forecast_id,
            w.station_name,
            f.forecast_date,
            f.predicted_temperature,
            f.predicted_humidity,
            f.heatwave_probability
        FROM Forecast f
        JOIN WeatherStation w
            ON f.station_id = w.station_id
        ORDER BY f.forecast_id DESC;
    """)

    forecasts = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "forecasts.html",
        forecasts=forecasts
    )


# ==========================================
# FEATURE 1: CITY / STATION COMPARISON
# ==========================================

@app.route("/comparison")
def comparison():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            w.station_id,
            w.station_name,
            r.region_name,
            MAX(s.temperature) AS maximum_temperature,
            MIN(s.temperature) AS minimum_temperature,
            ROUND(AVG(s.humidity), 2) AS average_humidity,
            COUNT(s.reading_id) AS reading_count
        FROM WeatherStation w
        LEFT JOIN Region r
            ON w.region_id = r.region_id
        LEFT JOIN SensorReading s
            ON w.station_id = s.station_id
        GROUP BY
            w.station_id,
            w.station_name,
            r.region_name
        ORDER BY w.station_name;
    """)

    comparison_rows = cursor.fetchall()

    cursor.close()
    conn.close()

    # Data for the comparison graphs
    chart_labels = [
        row[1] for row in comparison_rows
    ]

    chart_maximums = [
        float(row[3]) if row[3] is not None else None
        for row in comparison_rows
    ]

    chart_minimums = [
        float(row[4]) if row[4] is not None else None
        for row in comparison_rows
    ]

    chart_humidity = [
        float(row[5]) if row[5] is not None else None
        for row in comparison_rows
    ]

    # Convert query tuples to dictionaries for the HTML template
    comparison_rows = [
        {
            "station_id": row[0],
            "station_name": row[1],
            "region_name": row[2],
            "maximum_temperature": row[3],
            "minimum_temperature": row[4],
            "average_humidity": row[5],
            "reading_count": row[6]
        }
        for row in comparison_rows
    ]

    return render_template(
        "city_comparison.html",
        comparison_rows=comparison_rows,
        chart_labels=chart_labels,
        chart_maximums=chart_maximums,
        chart_minimums=chart_minimums,
        chart_humidity=chart_humidity
    )


# ==========================================
# FEATURE 2: HEATWAVE RISK DETECTION
# ==========================================

@app.route("/risk")
def risk():

    latest_readings = get_latest_station_readings()

    risk_rows = []

    risk_counts = {
        "Low": 0,
        "Moderate": 0,
        "High": 0,
        "Extreme": 0,
        "Unknown": 0
    }

    for row in latest_readings:

        # Tuple positions match get_latest_station_readings()
        temperature = row[7]
        risk_level = classify_heat_risk(temperature)

        risk_counts[risk_level] += 1

        risk_rows.append({
            "station_id": row[0],
            "station_name": row[1],
            "region_name": row[2],
            "reading_date": row[5],
            "reading_time": row[6],
            "temperature": temperature,
            "humidity": row[8],
            "wind_speed": row[9],
            "risk": risk_level,
            "risk_color": get_risk_color(risk_level)
        })

    # Display the highest-risk stations first
    risk_order = {
        "Extreme": 0,
        "High": 1,
        "Moderate": 2,
        "Low": 3,
        "Unknown": 4
    }

    risk_rows.sort(
        key=lambda item: risk_order[item["risk"]]
    )

    return render_template(
        "risk.html",
        risk_rows=risk_rows,
        risk_counts=risk_counts
    )


# ==========================================
# FEATURE 3: INTERACTIVE WEATHER MAP
# ==========================================

@app.route("/weather-map")
def weather_map():

    latest_readings = get_latest_station_readings()

    map_stations = []

    for row in latest_readings:

        latitude = row[3]
        longitude = row[4]

        # Skip stations without coordinates
        if latitude is None or longitude is None:
            continue

        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except (TypeError, ValueError):
            continue

        # Validate geographic coordinates
        if not (-90 <= latitude <= 90):
            continue

        if not (-180 <= longitude <= 180):
            continue

        temperature = row[7]
        humidity = row[8]
        risk_level = classify_heat_risk(temperature)

        map_stations.append({
            "station_id": row[0],
            "station_name": row[1],
            "region_name": row[2],
            "latitude": latitude,
            "longitude": longitude,
            "temperature": (
                float(temperature)
                if temperature is not None else None
            ),
            "humidity": (
                float(humidity)
                if humidity is not None else None
            ),
            "risk": risk_level,
            "risk_color": get_risk_color(risk_level)
        })

    return render_template(
        "weather_map.html",
        map_stations=map_stations
    )


# ==========================================
# RUN APPLICATION
# ==========================================

if __name__ == "__main__":
    app.run(debug=True)
