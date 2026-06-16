from pydantic import BaseModel, ConfigDict


class GroundednessResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metric_name: str = "groundedness"
    score: float
    explanation: str

