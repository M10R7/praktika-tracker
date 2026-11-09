"""
Pydantic schemas for Company.
"""

from pydantic import BaseModel, ConfigDict, Field


class CompanyBase(BaseModel):
    bin: str = Field(..., min_length=12, max_length=12, description="12-значный БИН организации")
    name: str = Field(..., min_length=2, max_length=255)
    legal_form: str = Field("ТОО", max_length=100)
    address: str = Field("г. Алматы", max_length=255)
    director_name: str | None = Field("", max_length=255)
    contact_person: str | None = Field("", max_length=255)
    contact_phone: str | None = Field("", max_length=50)
    contact_email: str | None = Field("", max_length=100)
    is_partner: bool = True


class CompanyCreate(CompanyBase):
    pass


class CompanyOut(CompanyBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
