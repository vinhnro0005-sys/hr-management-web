from pydantic import BaseModel, ConfigDict, Field


class DepartmentCreate(BaseModel):
    # Bỏ khoảng trắng ở đầu và cuối chuỗi
    model_config = ConfigDict(str_strip_whitespace=True)
    name: str = Field(
        min_length=1,
        max_length=100,
    )


class DepartmentUpdate(DepartmentCreate):
    pass
