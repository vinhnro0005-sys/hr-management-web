import re
from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator


class EmployeeBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=100)

    department_id: int = Field(gt=0)

    position: str | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, max_length=20)
    email: str | None = Field(default=None, max_length=255)
    address: str | None = Field(default=None, max_length=255)

    gender: Literal["Nam", "Nữ", "Khác"] | None = None

    birthday: date | None = None
    start_date: date | None = None

    @field_validator(
        "position",
        "phone",
        "email",
        "address",
        "gender",
        "birthday",
        "start_date",
        mode="before"
    )
    @classmethod
    def empty_value_to_none(cls, value):
        if isinstance(value, str):
            value = value.strip()

            if value == "":
                return None
        return value

    # Email phải có dạng ten@mien.tld
    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None):
        if value is None:
            return None

        pattern = r"[^@\s]+@[^@\s]+\.[^@\s]+"

        if re.fullmatch(pattern, value) is None:
            raise ValueError("Email không đúng định dạng")
        return value

    # Ngày sinh không được nằm trong tương lai
    @field_validator("birthday")
    @classmethod
    def validate_birthday(cls, value: str | None):
        if value is not None:
            if value > date.today():
                raise ValueError("Ngày sinh không được nằm trong tương lai")
        return value

    # Ngày vào làm không được trước ngày sinh
    @field_validator("start_date")
    @classmethod
    def validate_start_date(cls, value: str | None, info: ValidationInfo):
        birthday = info.data.get("birthday")

        if birthday is not None and value is not None:
            if value < birthday:
                raise ValueError("Ngày vào làm không được trước ngày sinh")
        return value


class EmployeeCreate(EmployeeBase):
    id: str = Field(min_length=1, max_length=20)


class EmployeeUpdate(EmployeeBase):
    pass
