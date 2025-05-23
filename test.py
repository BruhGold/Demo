import settings
import requests
import json

class Storage:
    def __init__(self):
        self.storage = {}

    def set(self, key, value):
        self.storage[key] = value

    def get(self, key):
        return self.storage.get(key)

    def delete(self, key):
        if key in self.storage:
            del self.storage[key]

class APIRequest:
    ACCESS_TOKEN_URL = f"{settings.DOMAIN}/api/token/"
    REFRESH_TOKEN_URL = f"{settings.DOMAIN}/api/token/refresh/"
    storage = Storage()

    def __init__(self, url, method, headers=None, params=None, payload=None):
        self.url = url
        self.method = method
        self.headers = headers or {}
        self.params = params or {}
        self.payload = payload or {}

    def send(self):
        access_token = self.storage.get("access_token")
        if access_token:
            self.headers["Authorization"] = f"Bearer {access_token}"
        
        if self.method == "GET":
            response = requests.get(self.url, headers=self.headers, params=self.params)
        elif self.method == "POST":
            response = requests.post(self.url, headers=self.headers, params=self.params, json=self.payload)
        else:
            raise ValueError(f"Unsupported HTTP method: {self.method}")

        return response.json()
        

    # The 2 methods below are for obtaining and refreshing the access token and storing it in the storage
    def GetAccessToken(self):
        payload = {
            "api_secret": "secret",
            "provider": "moodle",
            "uid": 1 # This should be replaced with the actual user ID
        }
        response = requests.post(self.ACCESS_TOKEN_URL, json=payload)
        if response.status_code == 200:
            self.storage.set("access_token", response.json().get("access"))
            self.storage.set("refresh_token", response.json().get("refresh"))
            return response.json()
        else:
            raise Exception("Failed to obtain access token")
    
    def TryRefreshToken(self):
        payload = {
            "refresh": self.storage.get("refresh_token")
        }
        response = requests.post(self.REFRESH_TOKEN_URL, json=payload)
        if response.status_code == 200:
            self.storage.set("access_token", response.json().get("access"))
            self.storage.set("refresh_token", response.json().get("refresh"))
            return response.json()
        else:
            raise Exception("Failed to refresh access token")
        
    def ClearTokens(self):
        self.storage.delete("access_token")
        self.storage.delete("refresh_token")
    
    def run(self):
        # Simulate running the request
        response = self.send()
        if response.get("code") == "token_not_valid":
            try:
                self.TryRefreshToken()
                response = self.send()
            except Exception as e:
                print(f"Error refreshing token: {e}")
                self.ClearTokens()
                try:
                    self.GetAccessToken()
                    response = self.send()
                except Exception as e:
                    print(f"Error obtaining new access token: {e}")
                    return self.send()  # Final attempt, anonymous
        return response

# inheriting from APIRequest to create a specific request
class GetProblemDetails(APIRequest):
    def __init__(self, problem_id):
        url = f"{settings.DOMAIN}/api/v2/problem/{problem_id}"
        method = "GET"
        headers = {"Content-Type": "application/json"}
        super().__init__(url, method, headers=headers)

# Example usage
if __name__ == "__main__":
    api_request = APIRequest(
        url=f"{settings.DOMAIN}/api/v2/problems",
        method="GET",
        headers={"Content-Type": "application/json"}
    )

    response = api_request.run()
    print(json.dumps(response, indent=4))

    print("\n\n ====================================================== \n\n")

    # Example usage of GetProblemDetails
    problem_id = "t12345"
    problem_request = GetProblemDetails(
        problem_id=problem_id
    )
    problem_response = problem_request.run()
    print(json.dumps(problem_response, indent=4))