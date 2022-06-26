import datetime
import os
import json
import traceback

import flask
from psycopg2 import pool

from jinja2 import Environment, FileSystemLoader
from kafka import KafkaProducer
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.kafka import KafkaInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
)

from utils import create_topic_if_not_exist

# initialize provider, jaeger exporter.
provider = TracerProvider(resource=Resource.create({SERVICE_NAME: 'api'}))
provider.add_span_processor(BatchSpanProcessor(JaegerExporter(agent_host_name='jaeger', agent_port=6831)))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)

# initialize flask app.
app = flask.Flask(__name__)
FlaskInstrumentor().instrument_app(app)
KafkaInstrumentor().instrument()
Psycopg2Instrumentor().instrument()

# initialize kafka topic
TOPIC_NAME = 'async-queue'
conf = dict(bootstrap_servers=os.environ.get('DEMO_BOOTSTRAP_SERVER', 'broker:9092'))
create_topic_if_not_exist(conf, TOPIC_NAME)
producer = KafkaProducer(**conf)

cnxpool = pool.SimpleConnectionPool(
    1, 20, user="postgres-user",
    password="postgres-pw",
    host="postgres",
    port="5432",
    database="example-db")


def query_database():
    data = []
    cnx = cnxpool.getconn()
    cursor = cnx.cursor()
    cursor.execute("""select "ST", "ED", "COUNT" from "T_PV_COUNT" order by "ST";""")
    for (st, ed, count) in cursor.fetchall():
        data.append({
            'st': datetime.datetime.fromtimestamp(st // 1000),
            'ed': datetime.datetime.fromtimestamp(ed // 1000),
            'count': count,
        })
    cursor.close()
    cnxpool.putconn(cnx)
    return data


@app.route('/')
def home():
    # send data to kafka for offline processing.
    producer.send(TOPIC_NAME, json.dumps({'url': '/'}).encode('utf-8'))

    try:
        # query aggregated data.
        data = query_database()
    except:
        print(traceback.format_exc())
        return "Please initialize pipeline first. See readme file.<br>Refresh this page in 1~2 seconds."

    # render to html with line chart.
    return Environment(
        loader=FileSystemLoader('.')).get_template(
        name='template.jinja').render(
        data=data), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)

# todo: add another api to trigger trace without windowed table -> stream. (Sink windowed table by value)
# todo: add error endpoint to show error trace.
