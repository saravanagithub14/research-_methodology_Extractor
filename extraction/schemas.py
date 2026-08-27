from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class Evidence(BaseModel):
    model_config = ConfigDict(extra="forbid")
    page: int | None = None
    section: str | None = None
    quote: str = Field(min_length=1, max_length=1000)
    block_id: str | None = None


class SoftwareTool(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    version: str | None = None
    parameters: dict[str, str | int | float | bool] = Field(default_factory=dict)
    status: Literal["reported", "ambiguous", "inferred"] = "reported"
    evidence: list[Evidence] = Field(min_length=1)


class Instrument(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    manufacturer: str | None = None
    model: str | None = None
    evidence: list[Evidence] = Field(min_length=1)


class Reagent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    manufacturer: str | None = None
    catalog_number: str | None = None
    concentration: str | None = None
    evidence: list[Evidence] = Field(min_length=1)


class Dataset(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = None
    accession: str | None = None
    database: str | None = None
    url: str | None = None
    evidence: list[Evidence] = Field(min_length=1)


class StatisticalMethod(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    purpose: str | None = None
    threshold: str | None = None
    multiple_testing_correction: str | None = None
    software: str | None = None
    evidence: list[Evidence] = Field(min_length=1)


class MethodologyExtraction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    software: list[SoftwareTool] = Field(default_factory=list)
    instruments: list[Instrument] = Field(default_factory=list)
    reagents: list[Reagent] = Field(default_factory=list)
    datasets: list[Dataset] = Field(default_factory=list)
    statistical_methods: list[StatisticalMethod] = Field(default_factory=list)
    method_steps: list["MethodStep"] = Field(default_factory=list)


class MethodStep(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    order: int = Field(ge=1)
    category: str
    action: str
    description: str
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    parameters: dict[str, str | int | float | bool] = Field(default_factory=dict)
    duration: str | None = None
    temperature: str | None = None
    predecessor_ids: list[str] = Field(default_factory=list)
    successor_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    evidence: list[Evidence] = Field(min_length=1)


MethodologyExtraction.model_rebuild()
