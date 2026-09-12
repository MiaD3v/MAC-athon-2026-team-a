import requests
import json
url = "https://api.data.gov/ed/collegescorecard/v1/schools?api_key=<key>&per_page=100&fields=school.name"



states = {
    "Alabama":1,
    "Alaska":2,
    "Arizona":4,
    "Arkansas":5,
    "California":6,
    "Colorado":8,
    "Connecticut":9,
    "Delaware":10,
    "District of Columbia":11,
    "Florida":12,
    "Georgia":13,
    "Hawaii":15,
    "Idaho":16,
    "Illinois":17,
    "Indiana":18,
    "Iowa":19,
    "Kansas":20,
    "Kentucky":21,
    "Louisiana":22,
    "Maine":23,
    "Maryland":24,
    "Massachusetts":25,
    "Michigan":26,
    "Minnesota":27,
    "Mississippi":28,
    "Missouri":29,
    "Montana":30,
    "Nebraska":31,
    "Nevada":32,
    "New Hampshire":33,
    "New Jersey":34,
    "New Mexico":35,
    "New York":36,
    "North Carolina":37,
    "North Dakota":38,
    "Ohio":39,
    "Oklahoma":40,
    "Oregon":41,
    "Pennsylvania":42,
    "Rhode Island":44,
    "South Carolina":45,
    "South Dakota":46,
    "Tennessee":47,
    "Texas":48,
    "Utah":49,
    "Vermont":50,
    "Virginia":51,
    "Washington":53,
    "West Virginia":54,
    "Wisconsin":55,
    "Wyoming":56,
}

east = [
    "Connecticut",
    "Maine",
    "Massachusetts",
    "New Hampshire",
    "Rhode Island",
    "Vermont",
    "New Jersey",
    "New York",
    "Pennsylvania",
]

midwest = [
    "Illinois",
    "Indiana",
    "Michigan",
    "Ohio",
    "Wisconsin",
    "Iowa",
    "Kansas",
    "Minnesota",
    "Missouri",
    "Nebraska",
    "North Dakota",
    "South Dakota",
]

south = [
    "Delaware",
    "District of Columbia",
    "Florida",
    "Georgia",
    "Maryland",
    "North Carolina",
    "South Carolina",
    "Virginia",
    "West Virginia",
    "Alabama",
    "Kentucky",
    "Mississippi",
    "Tennessee",
    "Arkansas",
    "Louisiana",
    "Oklahoma",
    "Texas",
]

west = [
    "Arizona",
    "Colorado",
    "Idaho",
    "Montana",
    "Nevada",
    "New Mexico",
    "Utah",
    "Wyoming",
    "Alaska",
    "California",
    "Hawaii",
    "Oregon",
    "Washington",
]

def APISearchByName(name):
    response = requests.get("https://api.data.gov/ed/collegescorecard/v1/schools?api_key=<>&per_page=100&school.name="+name)
    data = response.json()
    locale =  data["results"][0]['school']['locale']
    match locale:
        case 11, 12:
            locale = "City"
        case 21, 21:
            locale = "Suburban"
        case 13,23,31,32,33:
            locale = "Town"
        case 41,42,43:
            locale = "Rural"
    return data["results"][0]

def getCommaSeparatedListOfRegion(region,):
    out = ""
    for state in region:
        out += str(states[state]) + ","
    return out


def APISearchFull(params):
    response = requests.get(url+params)
    data = response.json()
        #goes through all pages and adds the results to the first dictionary
        #jank and gross but whatever
    for x in range(1, -(-int(data["metadata"]["total"]) // int(data["metadata"]["per_page"]))):
        response = requests.get(url+params+f"&page={x}")
        if response.status_code == 200:
            new_page = response.json()
            data["results"].append(new_page["results"])
        else:
            raise ValueError("Failed with status code: {response.status_code}")
    return data


def APISearchNameList(state = "", city = "", city_size = "", act_min = "",act_max="", \
                    sat_min="", sat_max="", enrollment_min="", enrollment_max="", region="", \
                    acceptance_min="", acceptance_max="", instate_min="", instate_max="", \
                    outstate_min="", outstate_max=""):
    params = ""
    if(state):
       params += f"&school.state_fips={states[state]}" 
    if(city):
        params += "&school.city=" + city
    if(city_size):
        match city_size:
            case "City":
                city_size = "11,12"
            case "Suburban":
                city_size = "21,22"
            case "Town":
                city_size = "13,23,31,32,33"
            case "Rural":
                city_size = "41,42,43"
            case _:
                pass
        params += "&school.locale=" + city_size
    if(act_min and act_max):
        params += f"&latest.admissions.act_scores.midpoint.cumulative__range={act_min}..{act_max}"
    if(sat_min and sat_max):
        params += f"&latest.admissions.sat_scores.average.overall__range={sat_min}..{sat_max}"
    if(enrollment_max and enrollment_min):
        params += f"&latest.student.size__range={enrollment_min}..{enrollment_max}&fields=school.name"
    if(region and not state):
        match region:
                case "east":
                    region = east
                    region_states = getCommaSeparatedListOfRegion(region)
                    params += "&school.state_fips=" + region_states
                case "west":
                    region = west
                    region_states = getCommaSeparatedListOfRegion(region)
                    params += "&school.state_fips=" + region_states
                case "south":
                    region = south
                    region_states = getCommaSeparatedListOfRegion(region)
                    params += "&school.state_fips=" + region_states
                case "midwest":
                    region = midwest
                    region_states = getCommaSeparatedListOfRegion(region)
                    params += "&school.state_fips=" + region_states
                case _: 
                    pass
    if(acceptance_max and acceptance_min):
        params += f"&latest.admissions.admission_rate.overall__range={acceptance_min}..{acceptance_max}"
    if(instate_min and instate_max):
        params += f"&latest.cost.tuition.in_state__range={instate_min}..{instate_max}"
    if(outstate_max and outstate_min):
        params += f"&latest.cost.tuition.out_of_state__range={outstate_min}..{outstate_max}"
    datalist = []
    try:
        for college in APISearchFull(params)["results"]:
            try:
                datalist.append(college["school.name"])
            except TypeError:
                pass # The api sometimes just gives us bad data :p
    except KeyError:
        return APISearchFull(params) # if you search by school name this doesn't work, deal with it later
    return datalist
