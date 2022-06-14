import datetime
import os
import json
import time

import flask
from mysql.connector.pooling import MySQLConnectionPool

import mysql
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

from kafka_utils import create_topic_if_not_exist

# Initialize provider, jaeger exporter.
provider = TracerProvider(
    resource=Resource.create({SERVICE_NAME: 'api'}))
provider.add_span_processor(
    BatchSpanProcessor(
        JaegerExporter(
            agent_host_name='jaeger', agent_port=6831)))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)

# Initialize flask app.
app = flask.Flask(__name__)
FlaskInstrumentor().instrument_app(app)
KafkaInstrumentor().instrument()
MySQLInstrumentor().instrument()

# Initialize kafka topic
conf = dict(bootstrap_servers=os.environ.get('DEMO_BOOTSTRAP_SERVER', 'kafka:9092'))
topic_name = 'async-queue'
create_topic_if_not_exist(conf, topic_name)
producer = KafkaProducer(**conf)

cnxpool = MySQLConnectionPool(
    pool_name="mypool",
    pool_size=10,
    user='example-user',
    password='example-pw',
    host='localhost',
    database='example-db')


@app.route('/')
def home():
    values = []

    cnx = cnxpool.get_connection()
    cursor = cnx.cursor()
    cursor.execute("select st, ed, count from PV_COUNT order by st;")
    for (st, ed, count) in cursor.fetchall():
        values.append({
            'st': datetime.datetime.fromtimestamp(st // 1000),
            'ed': datetime.datetime.fromtimestamp(ed // 1000),
            'count': count,
        })
    cursor.close()
    cnx.close()

    producer.send(topic_name, json.dumps({'hello': 'world'}).encode('utf-8'))

    file_loader = FileSystemLoader('.')
    env = Environment(loader=file_loader)
    template = env.get_template('template.jinja')

    return template.render(data=values), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
