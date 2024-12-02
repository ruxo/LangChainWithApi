from aiohttp import web

async def get_gps(req):
    return web.json_response({
        'latitude': 37.7749,
        'longitude': -122.4194
    })

app = web.Application()
app.add_routes([web.post('/ai/gps', get_gps)])

web.run_app(app, port=8000)