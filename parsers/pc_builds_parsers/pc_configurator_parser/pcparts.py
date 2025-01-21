from pcpartpicker_flask import API

api = API()
cpu_data = api.retrieve("cpu")
