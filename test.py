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
        elif self.method == "PUT":
            response = requests.put(self.url, headers=self.headers, params=self.params, json=self.payload)
        elif self.method == "DELETE":
            response = requests.delete(self.url, headers=self.headers, params=self.params)
        else:
            raise ValueError(f"Unsupported HTTP method: {self.method}")

        return response
        

    # The 2 methods below are for obtaining and refreshing the access token and storing it in the storage
    def GetAccessToken(self):
        payload = {
            "api_secret": settings.TOKEN_OBTAIN_SECRET,
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
        response = self.send() # Initial attempt, use old token in storage

        if response.status_code == 401:  # Unauthorized
            try:
                self.TryRefreshToken()
                response = self.send() # Retry with access token obtained from refresh token
            except Exception as e:
                print(f"Error refreshing token: {e}")
                self.ClearTokens()
                try:
                    self.GetAccessToken()
                    response = self.send() # Retry with new access token, if refresh token is invalid
                except Exception as e:
                    print(f"Error obtaining new access token: {e}")
                    if self.method in ["GET"]:
                        response = self.send()
                    else:
                        raise Exception("Cannot send authenticated request without valid token")

        return response.json()

# inheriting from APIRequest to create a specific request
class GetProblemDetails(APIRequest):
    def __init__(self, problem_id):
        url = f"{settings.DOMAIN}/api/v2/problem/{problem_id}"
        method = "GET"
        headers = {"Content-Type": "application/json"}
        super().__init__(url, method, headers=headers)

# Example of APIRequest that requires authentication
class UpdateProblem(APIRequest):
    def __init__(self, problem_id, payload):
        url = f"{settings.DOMAIN}/api/v2/problem/{problem_id}"
        method = "PUT"
        headers = {"Content-Type": "application/json"}
        super().__init__(url, method, headers=headers, payload=payload)

# Example usage
if __name__ == "__main__":
    # Example usage of APIRequest
    #api_request = APIRequest(
    #    url=f"{settings.DOMAIN}/api/v2/problems",
    #    method="GET",
    #    headers={"Content-Type": "application/json"}
    #)

    #print(api_request.storage.get("access_token"))

    #response = api_request.run()
    #print(json.dumps(response, indent=4, ensure_ascii=False))

    #print("\n\n ====================================================== \n\n")

    # Example usage of GetProblemDetails
    problem_id = "newproblem" # I can update the profile Language back to "en" if needed
    #problem_id = "t12345" # The user does not have permission to edit this problem, you can test it out
    #problem_request = GetProblemDetails(
    #    problem_id=problem_id
    #)

    #problem_response = problem_request.run()
    #print(json.dumps(problem_response, indent=4, ensure_ascii=False))

    #print("\n\n ====================================================== \n\n")

    # example of UpdateProblem
    payload = {
        #"code": "t12345",
        #"name": "Sample Problem Put",
        #"description": "Solve this simple problem.",
        #"authors": [1],  
        #"curators": [],  
        #"testers": [],  
        #"types": [1],  
        #"group": 1,
        #"is_public": True,
        #"organizations": [1]
    }
    update_problem_request = UpdateProblem(
        problem_id=problem_id,
        payload=payload
    )
    update_problem_response = update_problem_request.run()
    print(json.dumps(update_problem_response, indent=4, ensure_ascii=False))