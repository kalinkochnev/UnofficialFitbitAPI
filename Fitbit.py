import datetime
import urllib.parse
import re
import json
import requests


class FitbitAuth:
    token_url = 'https://api.fitbit.com/oauth2/token'
    authorize_url = 'https://www.fitbit.com/oauth2/authorize'

    def __init__(self, callback_url, client_id, client_secret):
        self.callback_url = callback_url
        self.client_id = client_id
        self.client_secret = client_secret


class FitbitDataInstance:
    fitbit_url = "https://api.fitbit.com"

    def __init__(self, FitbitAuth, data_scope, url, url_params):
        self.Fitbit = FitbitAuth
        self.data_scope = self.sort_scope(data_scope)
        self.resource_url = self.subPath(url, url_params)
        self.authorization_code = ""
        self.access_token = ""
        self.api_call_response = None

    @classmethod
    def todays_date(self):
        return datetime.datetime.now().strftime('%Y-%m-%d')

    @classmethod
    def custom_date(self, datetime_obj):
        return datetime_obj.strftime('%Y-%m-%d')

    def subPath(self, url, url_args):
        new_path = url
        for key, value in url_args.items():
            search_str = f"[{key}]"
            new_path = re.sub(re.escape(search_str), value, new_path)
        return self.fitbit_url + new_path

    # Possible scopes
    # ['activity', 'heartrate', 'location', 'nutrition', 'profile', 'settings', 'sleep', 'social', 'weight']
    def sort_scope(self, scope):
        return " ".join(sorted(scope))

    def get_auth_redirect(self):
        # A. simulate request from browser on the authorize_url - will return an auth code after the user accepts
        # https://www.fitbit.com/oauth2/authorize?response_type=code&client_id=22B79T&redirect_uri=https%3A%2F%2Fkalink.dev&scope=heartrate&expires_in=604800
        authorize_params = {
            'response_type': 'code',
            'client_id': self.Fitbit.client_id,
            'redirect_uri': self.Fitbit.callback_url,
            'scope': self.data_scope,
            'expires_in': 604800,
        }

        return str(
            'https://www.fitbit.com/oauth2/authorize?' + urllib.parse.urlencode(authorize_params, doseq=True).replace(
                '+', '%20'))

    def ask_for_url(self):
        # B. enter resource_url after clicking here for setting the code
        print(f'Click on this link and paste the redirected url {self.get_auth_redirect()}')
        return input()

    def parse_query(self, url):
        query_dict = urllib.parse.urlparse(url)
        return urllib.parse.parse_qs(query_dict.query)

    def get_code(self, query):
        # checks that the query dict has the code
        if 'code' in list(query.keys()):
            # further parse query, remove end hashtag
            self.authorization_code = query['code'][0]
        else:
            print('Code key not found in query dict')
            raise Exception('Code key not found in query dict')

    def get_access_token(self):
        headers = {
            'Authorization': 'Basic MjJCNzlUOmYyZDA1OTZhYWY0ZWRhYzI5Yzg4M2NiYmRmM2FkODgy',
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        data = {
            'grant_type': 'authorization_code',
            'code': self.authorization_code,
            'redirect_uri': self.Fitbit.callback_url,
            'clientId': self.Fitbit.client_id,
        }
        access_token_response = requests.post(FitbitAuth.token_url, data=data, headers=headers)

        # D. parse json for the access token, can use it as many times as we want within the request limits
        tokens = json.loads(access_token_response.text)
        self.access_token = tokens['access_token']

    def execute_request(self):
        code_url = self.ask_for_url()
        query = self.parse_query(code_url)
        self.get_code(query)
        self.get_access_token()
        
        # E. makes the data request using the given tokens and codes
        api_call_headers = {'Authorization': 'Bearer ' + self.access_token}
        self.api_call_response = requests.get(self.resource_url, headers=api_call_headers, verify=False)

    def print_response(self):
        json_print = json.loads(self.api_call_response.text)
        print(json.dumps(json_print, indent=4))
