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
    email: str = Field(min_length=1, max_length=255)
    address: str | None = Field(default=None, max_length=255)

    gender: Literal["Nam", "Nữ", "Khác"] | None = None

    birthday: date | None = None
    start_date: date | None = None

    @field_validator(
        "position",
        "phone",
        "address",
        "gender",
        "birthday",
        "start_date",
        mode="before"
    )
    @classmethod
    def empty_value_to_none(cls, value):
        if isinstance(value, str):
            value = " ".join(value.split())

            if value == "":
                return None
        return value
    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str):
        value = " ".join(value.split())
        for char in value:
            if not char.isalpha() and char != " ":
                raise ValueError("Họ và tên chỉ được chứa chữ cái")
        return value


    # Email phải có dạng ten@mien.tld
    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str):
        value = value.lower()
        pattern = r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}"

        if re.fullmatch(pattern, value) is None:
            raise ValueError("Email không đúng định dạng")
        return value
    #POSITION
    @field_validator("position")
    @classmethod
    def validate_position(cls, value: str | None):
        if value is None:
            return None
        return value.capitalize()

    #SDT
    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str | None):
        if value is None:
            return None
        pattern = r"\+?[0-9]{9,15}"
        if re.fullmatch(pattern, value) is None:
            raise ValueError("Số điện thoại không đúng định dạng")
        return value

    # Ngày sinh không được nằm trong tương lai
    @field_validator("birthday")
    @classmethod
    def validate_birthday(cls, value: date | None):
        if value is not None:
            today = date.today()
            if value > today:
                raise ValueError("Ngày sinh không được nằm trong tương lai")
            age = today.year - value.year
            if (today.month, today.day) < (value.month, value.day):
                age = age - 1
            if age < 18:
                raise ValueError("Nhân viên phải đủ 18 tuổi trở lên")
            if age > 100:
                raise ValueError("Ngày sinh không hợp lệ")
        return value

    # Ngày vào làm
    @field_validator("start_date")
    @classmethod
    def validate_start_date(cls, value: date | None, info: ValidationInfo):
        if value is not None:
            today = date.today()
            if value > today:
                raise ValueError("Ngày vào làm không được nằm trong tương lai")
            years_ago = today.year - value.year
            if(today.month, today.day) < (value.month, value.day):
                years_ago = years_ago - 1
            if years_ago > 60:
                raise ValueError("Ngày vào làm không hợp lệ")
        birthday = info.data.get("birthday")

        if birthday is not None and value is not None:
            if value < birthday:
                raise ValueError("Ngày vào làm không được trước ngày sinh")
            work_age = value.year - birthday.year
            if (value.month, value.day) < (birthday.month, birthday.day):
                work_age = work_age - 1
            if work_age < 18:
                raise ValueError("Nhân viên phải đủ 18 tuổi khi vào làm")
        return value


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(EmployeeBase):
    pass
