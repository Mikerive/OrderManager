from fastapi import FastAPI

from features.discord_integration.routes import router as discord_router
from features.user.routes import router as user_router

app = FastAPI()

# Include routers
app.include_router(discord_router)
app.include_router(user_router)

@app.get("/")
def read_root():
    return {"Hello": "World"}
