import os
import json

import flask
import requests
from kafka import KafkaProducer

from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.kafka import KafkaInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)

# Initialize provider, jaeger exporter.
from kafka_utils import create_topic_if_not_exist

provider = TracerProvider(resource=Resource.create({SERVICE_NAME: 'api'}))
provider.add_span_processor(
    BatchSpanProcessor(JaegerExporter(agent_host_name='localhost', agent_port=6831)))
trace.set_tracer_provider(provider)

# Initialize flask app.
app = flask.Flask(__name__)
FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()


def produce_hook(span, args, kwargs):
    if span and span.is_recording():
        span.set_attribute("flask-hook-attribute", "heyheyhey-flask")


KafkaInstrumentor().instrument(produce_hook=produce_hook)

# Get tracer.
tracer = trace.get_tracer(__name__)

# Initialize kafka topic
conf = dict(bootstrap_servers=os.environ.get('DEMO_BOOTSTRAP_SERVER', 'kafka:9092'))
topic_name = 'async-queue'
create_topic_if_not_exist(conf, topic_name)
producer = KafkaProducer(**conf)


@app.route('/')
def home():
    return requests.get('http://localhost:5001/internal-call').content, 200


@app.route('/internal-call')
def internal_call():
    # send dummy kafka message.
    producer.send(topic_name, json.dumps({'hello': 'world'}).encode('utf-8'))

    return json.dumps({}), 200


app.run(port=5001)
