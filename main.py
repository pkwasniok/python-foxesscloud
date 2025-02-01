import time
import hashlib
import urllib
import requests
import json

FOXESSCLOUD_URL = "https://www.foxesscloud.com"

class FoxessCloud:
    def __init__(self, key):
        self.key = key

    def getTimestamp(self):
        timestamp = round(time.time() * 1000)
        return timestamp

    def getSignature(self, path, key, timestamp):
        signature = fr'{path}\r\n{key}\r\n{timestamp}'
        print(signature)
        signature = hashlib.md5(signature.encode(encoding='UTF-8')).hexdigest()
        return signature

    def getHeaders(self, path, key):
        timestamp = self.getTimestamp()
        signature = self.getSignature(path, key, timestamp)

        headers = {
            "token": self.key,
            "timestamp": str(timestamp),
            "signature": signature,
            "lang": "en",
        }

        return headers

    def getURL(self, path):
        return urllib.parse.urljoin(FOXESSCLOUD_URL, path)

    def get(self, path):
        url = self.getURL(path)
        headers = self.getHeaders(path, self.key)

        response = requests.get(url, headers=headers)

        return response

    def post(self, path, data):
        url = self.getURL(path)
        headers = self.getHeaders(path, self.key)

        response = requests.post(url, headers=headers, json=data)

        return response

    def getRemainingRequests(self):
        response = self.get("/op/v0/user/getAccessCount")

        data = response.json()

        if data["errno"] != 0:
            return 0

        remainingRequests = int(data["result"]["remaining"])

        return remainingRequests

    def getInverters(self):
        response = self.post("/op/v0/device/list", {
            "currentPage": 1,
            "pageSize": 10,
        })

        data = response.json()

        if data["errno"] != 0:
            return []

        inverters = []
        for entry in data["result"]["data"]:
            inverter = Inverter(self, entry["deviceSN"], entry["deviceType"])
            inverters.append(inverter)

        return inverters

class Inverter:
    def __init__(self, foxess, serial, name):
        self.foxess = foxess
        self.serial = serial
        self.name = name
        self.variables = {}

    def __str__(self):
        return f'{self.serial} ({self.name})'

    def fetchAvailableVariables(self):
        response = self.foxess.get("/op/v0/device/variable/get")

        data = response.json()

        if data["errno"] != 0:
            return []

        for item in data["result"]:
            variableName = list(item.keys())[0]
            self.variables[variableName] = None

    def fetchVariables(self, variables):
        response = self.foxess.post("/op/v0/device/real/query", {
            "sn": self.serial,
            "variables": variables,
        })

        data = response.json()

        if data["errno"] != 0:
            return []

        for item in data["result"][0]["datas"]:
            variable = {
                "value": item["value"],
                "unit": item.get("unit"),
            }

            self.variables[item["variable"]] = variable

    def fetchAllAvailableVariables(self):
        self.fetchVariables(self.getAvailableVariables())

    def getAvailableVariables(self):
        return list(self.variables.keys())

    def getVariable(self, variable):
        return self.variables[variable]

    def getAllVariables(self):
        return self.variables

foxess = FoxessCloud("0e146dff-2e2e-4d56-b460-ac6cedb54bfe")

inverters = foxess.getInverters()
inverter = inverters[0]

inverter.fetchAvailableVariables()

inverter.fetchAllVariables()

variables = inverter.getAllVariables()
for name, variable in variables.items():
    if variable != None:
        print(f'{name}: {variable["value"]} {variable.get("unit")}')
    else:
        print(name, "N/A")

