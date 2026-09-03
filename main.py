from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
def home():
    return {"message": "HR Management System Demo"}

@app.get("/employees")
def employees():
    return {
        "Employees": [
            "Steve", "Flame"
        ]
    }
@app.post("/employees")
def employees_post():
    return {"message": "Employees created"}

@app.get("/employees/{employee_id}")
def get_employee(employee_id: int):
    return {"Employee ID": employee_id}

@app.get("/departments")
def get_departments():
    return {
        "departments": [
            "IT",
            "Human Resources",
            "Sales"
        ]
    }

@app.get("/about")
def about():
    return {
        "project": "HR Management",
        "backend": "FastAPI"
    }



# ----CHAY BANG UVICORN----
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)