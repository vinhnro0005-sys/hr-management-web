import uvicorn

from fastapi import FastAPI

from app.modules.department.department_router import router as department_router
from app.modules.employee.employee_router import router as employee_router

app = FastAPI()
app.include_router(department_router)
app.include_router(employee_router)


@app.get("/")
def home():
    return {"message": "HR Management System Demo"}


@app.get("/about")
def about():
    return {
        "project": "HR Management",
        "backend": "FastAPI"
    }



# ----CHAY BANG UVICORN----
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)