from pydantic import BaseModel, ConfigDict, Field
class DepartmentCreate(BaseModel):
    #bo khoang trang dau cuoi
    model_config = ConfigDict(str_strip_whitespace=True)
    #--
    name: str = Field(
        min_length=1,
        max_length=100,
    )

    #ke thua class tren
class DepartmentUpdate(DepartmentCreate):
    pass