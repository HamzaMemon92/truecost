from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone

from app.config import settings


class RedactingJsonFormatter(logging.Formatter):
    _sensitive = re.compile(r"(?i)(bearer\s+[\w.-]+|\+?\d{8,15}|[\w.+-]+@[\w.-]+|oauth[_-]?state=[^\s&]+)")
    _named_secret = re.compile(
        r"(?i)(\b(?:authkey|api[_-]?key|access[_-]?token|refresh[_-]?token|secret|otp)"
        r"(?:%22|[\"'])?\s*(?:=|:|%3D)\s*(?:%22|[\"'])?)([^\s&,}\"']+)"
    )
    _twilio_account_path = re.compile(r"(?i)(/Accounts/)[^/\s]+")

    def format(self, record: logging.LogRecord) -> str:
        message = self._sensitive.sub("[REDACTED]", record.getMessage())
        message = self._named_secret.sub(r"\1[REDACTED]", message)
        message = self._twilio_account_path.sub(r"\1[REDACTED]", message)
        return json.dumps({"timestamp": datetime.now(timezone.utc).isoformat(), "level": record.levelname, "logger": record.name, "message": message}, separators=(",", ":"))


def configure_observability() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(RedactingJsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)
    if settings.sentry_dsn:
        import sentry_sdk
        sentry_sdk.init(dsn=settings.sentry_dsn, environment=settings.app_env, send_default_pii=False, traces_sample_rate=0.1)


def instrument_app(app) -> None:
    if not settings.otel_exporter_otlp_endpoint:
        return
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    provider = TracerProvider(resource=Resource.create({"service.name": settings.app_name, "deployment.environment": settings.app_env}))
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint)))
    trace.set_tracer_provider(provider)
    from opentelemetry import metrics
    metrics.set_meter_provider(MeterProvider(resource=Resource.create({"service.name": settings.app_name, "deployment.environment": settings.app_env}), metric_readers=[PeriodicExportingMetricReader(OTLPMetricExporter(endpoint=settings.otel_exporter_otlp_endpoint))]))
    FastAPIInstrumentor.instrument_app(app)
