from pydantic import BaseModel, ConfigDict, Field, field_validator


class DepartmentCreate(BaseModel):
    #Bỏ khoảng trắng ở đầu và cuối chuỗi
    model_config = ConfigDict(str_strip_whitespace=True)
    name: str = Field(
        min_length=1,
        max_length=100,
    )

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value):
        if isinstance(value, str):
            value = " ".join(value.split())
        return value


class DepartmentUpdate(DepartmentCreate):
    pass
