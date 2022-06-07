import json

import flask
import requests

from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)

# Initialize provider, jaeger exporter.
provider = TracerProvider(resource=Resource.create({SERVICE_NAME: 'api->exporter'}))
provider.add_span_processor(
    BatchSpanProcessor(JaegerExporter(agent_host_name='localhost', agent_port=6831)))
trace.set_tracer_provider(provider)

# Initialize flask app.
app = flask.Flask(__name__)
FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()

# Get tracer.
tracer = trace.get_tracer(__name__)


@app.route('/')
def home():
    with tracer.start_as_current_span("INTERNAL HTTP CALL"):
        resp = requests.get('http://localhost:5001/internal-call').content, 200
    return resp


@app.route('/internal-call')
def internal_call():
    return json.dumps({}), 200


app.run(port=5001)
