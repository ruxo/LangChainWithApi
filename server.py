from fastapi import FastAPI

app = FastAPI()

@app.post("/ai/gps")
def get_gps():
    return {
        'latitude': 37.7749,
        'longitude': -122.4194
    }

