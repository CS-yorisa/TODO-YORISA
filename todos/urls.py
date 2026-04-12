from ninja import NinjaAPI

from todos.views import router

api = NinjaAPI()
api.add_router("/todos/", router)
