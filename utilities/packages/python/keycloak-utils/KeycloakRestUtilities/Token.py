import requests


def get_token(keycloak_endpoint: str, client_id: str, username: str, password: str) -> str:
    headers = {
        'Content-Type': "application/x-www-form-urlencoded"
    }
    form = {
        'grant_type': 'password',
        'username': username,
        'password': password,
        'client_id': client_id
    }
    response = requests.post(keycloak_endpoint, data=form, headers=headers)
    json_data = response.json()
    return json_data['access_token']


class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token: str):
        self.token = token

    def __call__(self, r: requests.PreparedRequest) -> requests.PreparedRequest:
        r.headers["authorization"] = "Bearer " + self.token
        return r
