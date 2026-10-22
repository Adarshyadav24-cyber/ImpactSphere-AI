"""Optional private API for ImpactSphere's validated preparedness plans."""
from __future__ import annotations

import json
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from plan_core import DemoProvider, PlanProvider, validate_plan_data


class PlanRequest(BaseModel):
    question: str = Field(min_length=3, max_length=120)


class Plan(BaseModel):
    title: str = Field(min_length=3, max_length=80)
    summary: str = Field(min_length=5, max_length=260)
    steps: list[str] = Field(min_length=2, max_length=5)
    provider: str


class BedrockProvider:
    """Uses the AWS SDK credential chain; credentials never come from the app."""

    name = "bedrock"

    def __init__(self, model_id: str, region: str):
        self.model_id = model_id
        self.region = region

    def generate(self, question: str) -> dict[str, object]:
        import boto3

        client = boto3.client("bedrock-runtime", region_name=self.region)
        response = client.converse(
            modelId=self.model_id,
            system=[{
                "text": (
                    "Create a short, general disaster-preparedness plan for a family. "
                    "Return only JSON with title, summary, and steps (2 to 5 short strings). "
                    "Do not claim live conditions, alerts, shelter availability, evacuation routes, "
                    "hospital status, or emergency phone numbers. Never replace local authorities. "
                    "Do not provide medical diagnosis or instructions for an active emergency."
                )
            }],
            messages=[{"role": "user", "content": [{"text": question}]}],
            inferenceConfig={"maxTokens": 600, "temperature": 0.2, "topP": 0.8},
        )
        raw = response["output"]["message"]["content"][0]["text"]
        # Do not execute tool calls or accept free-form model output as commands.
        try:
            data = json.loads(raw)
        except (TypeError, json.JSONDecodeError) as exc:
            raise ValueError("Bedrock returned non-JSON plan output") from exc
        data["provider"] = self.name
        return validate_plan_data(data)


def create_app(provider: PlanProvider | None = None) -> FastAPI:
    app = FastAPI(title="ImpactSphere Plan API", version="1.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )
    active_provider = provider or configured_provider()

    @app.get("/health")
    def health() -> dict[str, str]:
        # Do not expose AWS identity, credentials, or model account details.
        return {"status": "ok", "provider": active_provider.name}

    @app.post("/api/plan", response_model=Plan)
    def make_plan(body: PlanRequest) -> Plan:
        try:
            return Plan(**validate_plan_data(active_provider.generate(body.question)))
        except Exception as exc:
            # Avoid returning provider exception strings, which may include details.
            raise HTTPException(status_code=503, detail="Plan provider unavailable or returned invalid output") from exc

    return app


def configured_provider() -> PlanProvider:
    name = os.getenv("IMPACTSPHERE_PROVIDER", "demo").strip().lower()
    if name == "demo":
        return DemoProvider()
    if name == "bedrock":
        model_id = os.getenv("BEDROCK_MODEL_ID", "").strip()
        region = os.getenv("AWS_REGION", "").strip()
        if not model_id or not region:
            raise RuntimeError("BEDROCK_MODEL_ID and AWS_REGION must be set for Bedrock")
        return BedrockProvider(model_id, region)
    raise RuntimeError("IMPACTSPHERE_PROVIDER must be demo or bedrock")


app = create_app()
