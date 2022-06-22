import json
import os
import time

from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.kafka import KafkaInstrumentor
from kafka import KafkaProducer, KafkaConsumer

# initialize provider, jaeger exporter.
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

from utils import create_topic_if_not_exist

provider = TracerProvider(resource=Resource.create({SERVICE_NAME: 'app1'}))
provider.add_span_processor(BatchSpanProcessor(JaegerExporter(agent_host_name='jaeger', agent_port=6831)))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)

KafkaInstrumentor().instrument()

INPUT_TOPIC_NAME = 'async-queue'
OUTPUT_TOPIC_NAME = 'async-queue-enriched'
if __name__ == '__main__':

    conf = dict(bootstrap_servers=os.environ.get('DEMO_BOOTSTRAP_SERVER', 'broker:9092'))

    # make sure topic exist
    create_topic_if_not_exist(conf, INPUT_TOPIC_NAME)
    create_topic_if_not_exist(conf, OUTPUT_TOPIC_NAME)

    producer = KafkaProducer(**conf)
    consumer = KafkaConsumer(INPUT_TOPIC_NAME, group_id='my-group', **conf)

    # to demo how different languages handling traces.
    # this app will consume and produce data in python, downstream will be Java or some languages else.
    # instead of setup new span, it will extract tracingId from Kafka message header, and merge context.
    for message in consumer:

        ctx = None
        for kk, vv in message.headers:
            if kk == 'traceparent':
                tracing_id = vv.decode('utf-8')
                ctx = TraceContextTextMapPropagator().extract(
                    carrier={'traceparent': tracing_id})
                break

        with tracer.start_as_current_span(name='Otel-MergeContext', context=ctx):
            # todo: enriched data, calling multiple databases here.
            producer.send(OUTPUT_TOPIC_NAME, message.value)
