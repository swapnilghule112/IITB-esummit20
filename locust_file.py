from locust import HttpUser, TaskSet, task, between
import resource
import json

# for installation
# pip3 install locust


# to run type:
# locust -f locustfile.py

try:
    resource.setrlimit(resource.RLIMIT_NOFILE, (1000000, 1000000))
except:
    print("Couldn't raise resource limit")

class UserBehavior(TaskSet):

    @task
    def jwt_api(self):
        data = {
        'client_id': 'houdini',
        'client_secret': 'houdini'
        }

        headers = {
        "Content-Type": "application/json"
        }

        response = self.client.post(url="/api/v1/services/auth/",
                                    data=data,
                                    headers=headers)
        print(response.text)

class WebsiteUser(HttpUser):
    task_set = UserBehavior
    wait_time = between(5, 15)