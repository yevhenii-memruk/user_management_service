from fastapi import FastAPI
import uvicorn
app = FastAPI()


@app.get("/")
def read_root():
   return {"message": "Hello, world!"}


if __name__ == "__main__":
   uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)