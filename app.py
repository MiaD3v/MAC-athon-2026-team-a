from flask import Flask, render_template, request
from wtforms import Form, IntegerField, SubmitField, StringField, SelectField, validators
from API_Functions import APISearchNameList, APISearchByName
import requests
import serpapi

client = serpapi.Client(api_key="<key>")
def getImage(name):
    results = client.search({
      "engine": "google_images_light",
      "q": name,
      "image_type": "photo",
    })
    images_results = results["images_results"]
    imglink = images_results[1]["original"]
    for image in images_results[:5]:
      if "usnews.com" in image["original"]:
        imglink = image["original"]
        break
    return imglink

api_key = "<key>"
api_url = "http://api.weatherapi.com/v1"

def getWeatherAtZip(zipcode):
    with requests.request("GET", f"{api_url}/current.json?key={api_key}&q={zipcode}") as r:
        return r.json()

app = Flask(__name__)

class CollegeSurveyForm(Form):
    # TODO: need more validators
    city = StringField("City:", [validators.Optional()])
    school_size = IntegerField("School Size (# Undergrad):", [validators.Optional()])
    act_score = IntegerField("ACT Scores:", [validators.Optional()])
    sat_score = IntegerField("SAT Scores:", [validators.Optional()])
    state = StringField("State:", [validators.Optional()])
    region = \
        SelectField("Region:",      \
                    choices=[
                        "",   \
                        "East",    \
                        "West",    \
                        "South",   \
                        "MidWest", \
                        "Other"])
    city_type = \
            SelectField("City Type:",      \
                        choices=[   
                            "",   \
                            "City",    \
                            "Suburban",    \
                            "Town",   \
                            "Rural",])
    acceptance_min = \
        IntegerField("Minimum Acceptance Rate:", \
        [validators.NumberRange(min=0, max=100, message="Acceptance rate must be between 0 and 100"), validators.Optional()])
    acceptance_max = \
        IntegerField("Maximum Acceptance Rate:", \
        [validators.NumberRange(min=0, max=100, message="Acceptance rate must be between 0 and 100"), validators.Optional()])
    instate_min = IntegerField("Minimum In-State Tuition:", [validators.Optional()])
    instate_max = IntegerField("Maximum In-State Tuition:", [validators.Optional()])
    outstate_min = IntegerField("Minimum Out-of-State Tuition:", [validators.Optional()])
    outstate_max = IntegerField("Maximum Out-of-State Tuition:", [validators.Optional()])
    submit_field = SubmitField("Submit")

@app.route("/")
def beforeStart():
    return render_template("homePage.html")

@app.route("/survey/", methods=["GET", "POST"])
def root():
    form = CollegeSurveyForm(request.form)
    if request.method == "POST" and form.validate():
        names = \
        APISearchNameList("" if form.state.data is None else form.state.data,
                          "" if form.city.data is None else form.city.data,
                          "" if form.city_type.data is None else form.city_type.data,
                          "0" if form.act_score.data is None else str(form.act_score.data),
                          "36",
                          "400" if form.sat_score.data is None else str(form.sat_score.data),
                          "1600",
                          "0" if form.school_size.data is None else str(form.school_size.data),
                          "9999999",
                          str(form.region.data).lower(),
                          "0" if form.acceptance_min.data is None else str(form.acceptance_min.data/100),
                          "1" if form.acceptance_max.data is None else str(form.acceptance_max.data/100),
                          "0" if form.instate_min.data is None else str(form.instate_min.data),
                          "9999999" if form.instate_max.data is None else str(form.instate_max.data),
                          "0" if form.outstate_min.data is None else str(form.outstate_min.data),
                          "9999999" if form.outstate_max.data is None else str(form.outstate_max.data))
        colleges = []
        for name in names:
            college_data = APISearchByName(name)
            to_add = {
                "imglink": getImage(name),
                "general": {
                    "Name": name,
                    "State": "N/A",
                    "City": "N/A",
                    "City Size": "N/A",
                    "ACT Scores": "N/A",
                    "SAT Scores": "N/A",
                    "Enrollment": "N/A",
                    "Acceptance": "N/A",
                    "In-State Tuition": "N/A",
                    "Out-of-State Tuition": "N/A",
                },
                "weather": {
                    "Temp (°F)": "N/A",
                    "Feels Like (°F)": "N/A",
                    "UV Index": "N/A",
                    "Humidity (%)": "N/A",
                    "Wind (MPH)": "N/A",
                    "Wind (°)": "N/A",
                },
            }
            try:
                to_add["general"]["State"] = college_data["school"]["state_fips"]
            except KeyError:
                pass
            try:
                to_add["general"]["City"] = college_data["school"]["city"]
            except KeyError:
                pass
            try:
                size = "N/A"
                match int(college_data["school"]["locale"]):
                    case 11 | 12:
                        size = "City"
                    case 21 | 21:
                        size = "Suburban"
                    case 13|23|31|32|33:
                        size = "Town"
                    case 41|42|43:
                        size = "Rural"
                to_add["general"]["City Size"] = size
            except KeyError:
                pass
            try:
                to_add["general"]["ACT Scores"] = college_data['latest']['admissions']['act_scores']['midpoint']['cumulative']
            except KeyError:
                pass
            try:
                to_add["general"]["SAT Scores"] = college_data['latest']['admissions']['sat_scores']['average']['overall']
            except KeyError:
                pass
            try:
                to_add["general"]["Enrollment"] = college_data['latest']['student']['size']
            except KeyError:
                pass
            try:
                to_add["general"]["Acceptance"] = college_data['latest']['admissions']['admission_rate']['overall']*100
            except KeyError:
                pass
            try:
                to_add["general"]["In-State Tuition"] = "$"+str(college_data['latest']['cost']['tuition']['in_state'])
            except KeyError:
                pass
            try:
                to_add["general"]["Out-of-State Tuition"] = "$"+str(college_data['latest']['cost']['tuition']['out_of_state'])
            except KeyError:
                pass
            weather = {}
            zipcode = ""
            try:
                zipcode = str(college_data["school"]["zip"])
            except KeyError:
                pass
            else:
                weather = getWeatherAtZip(zipcode)
                try:
                    to_add["weather"]["Temp (°F)"] = weather["current"]["temp_f"],
                except KeyError:
                    pass
                try:
                    to_add["weather"]["Feels Like (°F)"] = weather["current"]["feelslike_f"],
                except KeyError:
                    pass
                try:
                    to_add["weather"]["UV Index"] = weather["current"]["uv"],
                except KeyError:
                    pass
                try:
                    to_add["weather"]["Humidity (%)"] = weather["current"]["humidity"],
                except KeyError:
                    pass
                try:
                    to_add["weather"]["Wind (MPH)"] = weather["current"]["wind_mph"],
                except KeyError:
                    pass
                try:
                    to_add["weather"]["Wind (°)"] = weather["current"]["wind_degree"],
                except KeyError:
                    pass
                print(weather)
            colleges.append(to_add)
        return render_template("results.html", colleges=colleges)
    elif request.method == "POST" and not form.validate():
        return "not validate", 400
    return render_template("index.html", form=form)

if __name__ == "__main__":
    app.run()

