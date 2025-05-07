from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import member, container, school, division, caddy

app = FastAPI()

# CORS 설정 (FE가 localhost:5173에서 열리므로)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://testsimprec.duckdns.org","http://118.39.27.92"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(member.router)
app.include_router(container.router)
app.include_router(school.router)
app.include_router(division.router)
app.include_router(caddy.router) # 캐디


@app.get("/")
def root():
    return {"message": "Hello from FastAPI"}
