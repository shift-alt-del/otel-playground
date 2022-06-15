import datetime
import os
import json

import flask
from mysql.connector.pooling import MySQLConnectionPool

from jinja2 import Environment, FileSystemLoader
from kafka import KafkaProducer
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.mysql import MySQLInstrumentor
from opentelemetry.instrumentation.kafka import KafkaInstrumentor
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
MySQLInstrumentor().instrument()

# initialize kafka topic
TOPIC_NAME = 'async-queue'
conf = dict(bootstrap_servers=os.environ.get('DEMO_BOOTSTRAP_SERVER', 'broker:9092'))
create_topic_if_not_exist(conf, TOPIC_NAME)
producer = KafkaProducer(**conf)

# https://dev.mysql.com/doc/connector-python/en/connector-python-examples.html
cnxpool = MySQLConnectionPool(
    pool_name="mypool",
    pool_size=10,
    user='example-user',
    password='example-pw',
    host='mysql',
    database='example-db')


def query_database():
    data = []
    cnx = cnxpool.get_connection()
    cursor = cnx.cursor()
    cursor.execute("select st, ed, count from T_PV_COUNT order by st;")
    for (st, ed, count) in cursor.fetchall():
        data.append({
            'st': datetime.datetime.fromtimestamp(st // 1000),
            'ed': datetime.datetime.fromtimestamp(ed // 1000),
            'count': count,
        })
    cursor.close()
    cnx.close()
    return data


@app.route('/')
def home():
    # send data to kafka for offline processing.
    producer.send(TOPIC_NAME, json.dumps({'url': '/'}).encode('utf-8'))

    # query aggregated data.
    data = query_database()

    # render to html with line chart.
    return Environment(
        loader=FileSystemLoader('.')).get_template(
        name='template.jinja').render(
        data=data), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
