import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from api.auth import router as auth_router
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
    "http://localhost:5173",
    "https://localhost:5173",
    "https://127.0.0.1:5173",
    "https://127.0.0.1:5173",
    "https://reshpay.com",
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


