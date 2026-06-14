from fastapi import FastAPI

app = FastAPI(title="DeliverIQ", version="0.1.0")


@app.get("/")
def root():
    return {"status": "alive", "service": "DeliverIQ"}


@app.get("/health")
def health():
    return {"status": "ok"}
