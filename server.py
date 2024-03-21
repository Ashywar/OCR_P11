import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, flash, url_for


def is_competition_available(competition):
    now = datetime.now()
    comp_date = datetime.strptime(competition["date"], "%Y-%m-%d %H:%M:%S")
    if comp_date < now:
        competition["available"] = False
    else:
        competition["available"] = True
    return competition


# Function to load clubs from the 'clubs.json' file
def loadClubs():
    with open("clubs.json") as c:
        listOfClubs = json.load(c)["clubs"]
        return listOfClubs


# Function to load competitions from the 'competitions.json' file
def loadCompetitions():
    with open("competitions.json") as comps:
        listOfCompetitions = json.load(comps)["competitions"]
        # Checking if competition is past or not
        _listOfCompetitions = [is_competition_available(c) for c in listOfCompetitions]
        return _listOfCompetitions


app = Flask(__name__)
app.secret_key = "something_special"

# Load initial data for clubs and competitions
competitions = loadCompetitions()
clubs = loadClubs()


# Route: Render the index.html template
@app.route("/")
def index():
    return render_template("index.html")


# Route: Handle form submission for displaying club summary
@app.route("/showSummary", methods=["POST", "GET"])
def showSummary():
    if request.method == "POST":
        try:
            club = [c for c in clubs if c["email"] == request.form["email"]][0]
            return render_template("welcome.html", club=club, competitions=competitions)

        except IndexError:
            flash("Please enter a valid email")
            return redirect(url_for("index"))

    if request.method == "GET":
        # Retrieve the club data
        club_name = request.args.get("club")
        club = [c for c in clubs if c["name"] == club_name][0]
        if club is not None:
            return render_template("welcome.html", club=club, competitions=competitions)
        else:
            return redirect(url_for("index"))


# Route: Display the booking page for a specific competition and club
@app.route("/book/<competition>/<club>")
def book(competition, club):
    # Find the club and competition based on the provided names
    foundClub = [c for c in clubs if c["name"] == club][0]
    foundCompetition = [c for c in competitions if c["name"] == competition][0]
    if foundCompetition["available"] is False:
        flash("This competition is not available")
        return render_template("welcome.html", club=club, competitions=competitions)
    if foundClub and foundCompetition:
        return render_template(
            "booking.html", club=foundClub, competition=foundCompetition
        )
    else:
        flash("Something went wrong-please try again")
        return render_template("welcome.html", club=club, competitions=competitions)


# Route: Handle form submission for purchasing places
@app.route("/purchasePlaces", methods=["POST"])
def purchasePlaces():
    # Maximum places a user can book
    MAXPLACES = 12
    # Retrieve competition and club based on form data
    competition = [c for c in competitions if c["name"] == request.form["competition"]][
        0
    ]
    club = [c for c in clubs if c["name"] == request.form["club"]][0]
    # Extract relevant data
    club_points = int(club["points"])
    placesRequired = int(request.form["places"])
    placesAvailable = int(competition["numberOfPlaces"])

    # Check if the competition is available
    if competition["available"] is False:
        flash("This competition is not available")
        return render_template("welcome.html", club=club, competitions=competitions)

    # Check if placesRequested exceeds the maximum allowed
    if placesRequired > MAXPLACES:
        flash("You cannot book more than 12 places for a competition")
        return render_template("welcome.html", club=club, competitions=competitions)

    # Check if the user has enough points
    elif placesRequired > club_points:
        flash(
            f"You don't have enough points ({club_points}) to redeem {placesRequired} places"
        )
        return render_template("welcome.html", club=club, competitions=competitions)

    # Check if the requested places exceed the available places for the competition
    elif placesRequired > placesAvailable:
        flash(
            f"You are trying to redeem {placesRequired} places, which is more than available ({placesAvailable})"
        )
        return render_template("welcome.html", club=club, competitions=competitions)

    # Process the booking
    else:
        competition["numberOfPlaces"] = (
            int(competition["numberOfPlaces"]) - placesRequired
        )
        # Mark competition as not available if placesAvailable becomes zero
        if int(competition["numberOfPlaces"]) < 1:
            competition["available"] = False
        club["points"] = int(club["points"]) - (placesRequired)
        flash("Booking complete!")
        return render_template("welcome.html", club=club, competitions=competitions)


@app.route("/public_board")
def boardPublic():
    return render_template("public_board.html", clubs=clubs)


# Route: Handle user logout
@app.route("/logout")
def logout():
    return redirect(url_for("index"))
