from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
import requests
import os
from dotenv import load_dotenv

load_dotenv()
db = SQLAlchemy()

# Creating the database to store the locations
class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    area = db.Column(db.String(100), nullable=False)

def create_app():
    app = Flask(__name__)

    # Initializes the dbs and silents the warning
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(os.path.dirname(__file__), "locations.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

    # Connects the db
    db.init_app(app)

    def get_weather_data(city):
        API_KEY = os.getenv("API_KEY")
        URL = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid=" + API_KEY
        response = requests.get(URL).json()
        return response

    # GET method for when they input a city 
# Combine both decorators into a single route decorator
    @app.route("/", methods=["GET", "POST"])
    def index():
        if request.method == "POST":
            new_city = request.form.get("city_name").title()
            message = ""

            if new_city:
                city_exists = Location.query.filter_by(area=new_city).first()

                if not city_exists:
                    new_data = get_weather_data(new_city)

                    if new_data["cod"] == 200:
                        # Create a new location associated with the user or None if not authenticated
                        nco = Location(area=new_city)
                        db.session.add(nco)
                        db.session.commit()
                    else:
                        message = "City Is Not Real"
                else:
                    message = "City Is Already There"

                if message:
                    flash(message, "error")
                else:
                    flash("Success")

                return redirect(url_for("index"))

        # Handle the GET
        cities = Location.query.all()

        weather_data = list()

        for city in cities:
            try:
                response = get_weather_data(city.area)

                data = {
                    "id": city.id,
                    "city": city.area,
                    "temperature": convert_to_fahrenheit(response["main"]["temp"]),
                    "description": response["weather"][0]["description"],
                    "icon": response["weather"][0]["icon"]
                }

                weather_data.append(data)
            except Exception as e:
                print(f"Error processing weather data for {city.area}: {e}")

        return render_template("weather.html", weather_data=weather_data)


    # POST method (add to db) for when they 
    @app.route("/", methods=["POST"])
    def home_post():
        new_city = request.form.get("city_name").title()
        message = ""

        if new_city:
            city_exists = Location.query.filter_by(area=new_city).first()

            if not city_exists:
                new_data = get_weather_data(new_city)

                if new_data["cod"] == 200:
                    # Create a new location associated with the user or None if not authenticated
                    nco = Location(area=new_city)
                    db.session.add(nco)
                    db.session.commit()
                else:
                    message = "City Is Not Real"
            else:
                message = "City Is Already There"

        if message:
            flash(message, "error")
        else:
            flash("Success")

        return redirect(url_for("index"))

    # Handles Delete (POST method)
    @app.route('/delete/<int:id>', methods=['POST'])
    def delete(id):
        weather_entry = Location.query.get_or_404(id)

        try:
            db.session.delete(weather_entry)
            db.session.commit()
            flash("City Deleted")
        except Exception as e:
            flash(f"There Was A Problem Deleting The City: {str(e)}")

        return redirect(url_for('index'))

    # Handles Delete (DELETE method)
    @app.route('/delete/<int:id>', methods=['DELETE'])
    def delete_method(id):
        weather_entry = Location.query.get_or_404(id)

        try:
            db.session.delete(weather_entry)
            db.session.commit()
            flash("City Deleted")
        except Exception as e:
            flash(f"There Was A Problem Deleting The City: {str(e)}")

        return jsonify({"status": "success"})

    return app


def convert_to_fahrenheit(data):
    return round((data - 273.15) * (9/5) + 32)

if __name__ == "__main__":
    app = create_app()

    with app.app_context():
        db.create_all()

    app.run(debug=True)
