import requests
import json
import pyttsx3
import re
import speech_recognition as sr
import threading
import time


API_KEY = 'tOFvbMwRnf9J'
PROJECT_TOKEN = 'tphFHSzRKr8E'
RUN_TOKEN = 't4NEgkhRZKZp'


class Data:
    def __init__(self, api_key, project_token):
        self.api_key = api_key
        self.project_token = project_token
        self.params = {
            'api_key': self.api_key
        }
        self.data = self.get_data()

    def get_data(self):
        response = requests.get(f'https://www.parsehub.com/api/v2/projects/{self.project_token}/last_ready_run/data',
                                params=self.params)
        data = json.loads(response.text)
        return data

    def get_total_cases(self):
        """
        Returns the total amount of corona virus cases in the world.
        """
        data = self.data['Totals']

        for content in data:
            if content['name'] == 'Coronavirus Cases:':
                return content['Values']

    def get_total_deaths(self):
        """
        Returns the total amount of deaths due to the corona virus in the world
        """
        data = self.data['Totals']

        for content in data:
            if content['name'] == 'Deaths:':
                return content['Values']

    def get_total_recovered(self):
        """
        Returns the total amount of people who have successfully recovered from the coronavirus in the world.
        """
        data = self.data['Totals']

        for content in data:
            if content['name'] == 'Recovered:':
                return content['Values']

    def get_death_rate(self, country=None):
        """
        Returns the death rate of those who get the corona virus in the world or in a specific country.
        """
        if not country:
            output_text = ""
            cases = convert_to_num(self.get_total_cases())
            deaths = convert_to_num(self.get_total_deaths())

        else:
            output_text = "in {}".format(country)
            cases = convert_to_num(self.get_country_data(country)['total_cases'])
            deaths = convert_to_num(self.get_country_data(country)['total_deaths'])

        return "The death rate {} is {:.2f}%".format(output_text, ((deaths / cases) * 100))

    def get_recovery_rate(self, country=None):
        """
        Returns the recovery rate of those who get the corona virus in the world or in a specific country.
        """
        if not country:
            output_text = ""
            cases = convert_to_num(self.get_total_cases())
            recoveries = convert_to_num(self.get_total_recovered())

        else:
            output_text = "in {}".format(country)
            cases = convert_to_num(self.get_country_data(country)['total_cases'])
            recoveries = convert_to_num(self.get_country_data(country)['total_recovered'])

        return "The Recovery Rate {} is {:.2f}%".format(output_text, float((recoveries / cases) * 100))

    def get_country_data(self, country):
        """
        Returns the data for a specific country
        """
        data = self.data['country']

        for content in data:
            if content['name'].lower() == country.lower():
                return content

        return "0"

    def get_list_of_countries(self):
        """
        Returns a list of all countries that have been affected by the corona virus
        """
        countries = [country['name'].lower() for country in self.data['country']]
        return countries

    def update_data(self):
        response = requests.post(f'https://www.parsehub.com/api/v2/projects/{self.project_token}/run',
                                 params=self.params)

        def poll():
            time.sleep(0.1)
            old_data = self.data
            while True:
                new_data = self.get_data()
                if new_data != old_data:
                    self.data = new_data
                    print("Data Updated")
                    break
                time.sleep(5)

        t = threading.Thread(target=poll)
        t.start()


def convert_to_num(val):
    """
    Converts the string values scraped from the web page into numbers.
    """
    return float(val.replace(",", ""))


def speak(text):
    """
    Functions as a way for the computer to speak/answer questions asked.
    """
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()


def get_audio():
    """
    Function which receives audio from the user.
    """
    r = sr.Recognizer()
    with sr.Microphone() as source:
        audio = r.listen(source)
        said = ""

        try:
            said = r.recognize_google(audio)
        except Exception as e:
            print("Exception: {}".format(str(e)))

        return said.lower()


def main():
    """
    Main script.
    """

    print("Started Program.")
    end_word = 'stop'
    data = Data(API_KEY, PROJECT_TOKEN)
    data.update_data()
    country_list = data.get_list_of_countries()

    total_patterns = {
        re.compile("[\w\s]+ total [\w\s]+ cases"): data.get_total_cases,  # total cases
        re.compile("[\w\s]+ total cases"): data.get_total_cases,  # total cases
        re.compile("[\w\s]+ total [\w\s]+ deaths"): data.get_total_deaths,  # total deaths
        re.compile("[\w\s]+ total deaths"): data.get_total_deaths,  # total deaths
        re.compile("[\w\s]+ total [\w\s]+ death rate"): data.get_death_rate,  # total death rate
        re.compile("[\w\s]+ total death rate"): data.get_death_rate,  # total death rate
        re.compile("[\w\s]+ total [\w\s]+ recovered"): data.get_total_recovered,  # total recovered
        re.compile("[\w\s]+ total recovered"): data.get_total_recovered,  # total recovered
        re.compile("[\w\s]+ total recovery rate"): data.get_recovery_rate  # total recovery rate

    }

    country_patterns = {
        re.compile("[\w\s]+ cases [\w\s]+"): lambda country: data.get_country_data(country)['total_cases'],
        re.compile("[\w\s]+ deaths [\w\s]+"): lambda country: data.get_country_data(country)['total_deaths'],
        re.compile("[\w\s]+ recovered [\w\s]+"): lambda country: data.get_country_data(country)['total_recovered'],
        re.compile("[\w\s]+ recovery rate [\w\s]+"): data.get_recovery_rate,  # recovery rate in a country
        re.compile("[\w\s]+ death rate [\w\s]+"): data.get_death_rate  # death rate in a country
    }

    # make a way to display graphs of cases by dates in given country
    graph_patterns = {}


    update_command = "update"

    while True:
        print("listening...")
        # text = get_audio()
        text = 'how many recovered in canada'
        print(text)
        result = None

        for pattern, func in country_patterns.items():
            if pattern.match(text):
                words = set(text.split(" "))
                for country in country_list:
                    if country in words:
                        result = func(country)
                        break

        for pattern, func in total_patterns.items():
            if pattern.match(text):
                result = func()
                break

        if text == update_command:
            result = "Data is being updated. This may take a moment"
            data.update_data()

        if result:
            speak(result)
            print(result)

        if text.find(end_word) != -1:  # stops loop
            print("Exit")
            break


main()
