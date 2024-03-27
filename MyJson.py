import json

class MyJson:
    def __init__(self):
        pass

    def jsonParser(self, file):
        # Opening JSON file
        f = open(file)
        data = json.load(f)
        f.close()

        return data