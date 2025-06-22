import uvicorn
from fastapi import FastAPI
from api.auth import router as auth_router
from api.user.router import router as user_router
from api.buyer.router import router as buyer_router
from api.coop.router import router as coop_router
from api.expenditure.router import router as expenditure_router
from api.location.router import router as location_router
from fastapi.middleware.cors import CORSMiddleware
# import NotFoundError




app = FastAPI(
    docs_url="/docs",
    redoc_url="/redocs",
    title="My Business Backend",
    descriptiion="FastApi project for my business",
    version="1.0",
)


origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://odamefarms.netlify.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# @app.on_event("startup")
# async def startup():
#     await database.connect()


# @app.on_event("shutdown")
# async def shutdown():
#     await database.disconnect()


app.include_router(auth_router.router)
# app.add_middleware(NotFoundError)
app.include_router(user_router)
app.include_router(coop_router)
app.include_router(buyer_router)
app.include_router(expenditure_router)
app.include_router(location_router)


@app.get("/")
async def read_root():
    return "Welcome to the Farm Backend"


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="localhost",
        port=8000,
        reload=True,
    )


