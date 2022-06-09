import json
import os
import time

from kafka.admin import NewTopic
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.kafka import KafkaInstrumentor
from kafka import KafkaProducer, KafkaConsumer

# Initialize provider, jaeger exporter.
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace import TracerProvider

from kafka_utils import create_topic_if_not_exist

provider = TracerProvider(resource=Resource.create({SERVICE_NAME: 'offline-stage-1'}))
provider.add_span_processor(
    BatchSpanProcessor(JaegerExporter(agent_host_name='localhost', agent_port=6831)))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)


def consume_hook(span, record, args, kwargs):
    if span and span.is_recording():
        span.set_attribute("kafka-consumer-hook-attribute", "heyheyhey-got-from-flask")


# instrument kafka with produce and consume hooks
KafkaInstrumentor().instrument(consume_hook=consume_hook)

conf = dict(bootstrap_servers=os.environ.get('DEMO_BOOTSTRAP_SERVER', 'kafka:9092'))

# make sure topic exist
input_topic = 'async-queue'
output_topic = 'converted'
create_topic_if_not_exist(conf, input_topic)
create_topic_if_not_exist(conf, output_topic)

producer = KafkaProducer(**conf)
consumer = KafkaConsumer(input_topic, group_id='my-group', **conf)
for message in consumer:
    print(message)
    # time.sleep(0.2)
    producer.send(output_topic, json.dumps({'foo': 'bar'}).encode('utf-8'))
