# Otel Playground

## How to play
- API Service -> Kafka -> Apps -> KafkaStreams End-To-End distributed tracing.
- Access http://localhost:5001 to trigger kafka write.
- Access http://localhost:16686 to play with tracings on Jaeger UI.

Trace API writes Kafka.
![TraceOnline](images/trace_online.png)

Trace Kafka down stream microservices.
![TraceOffline](images/trace_offline.png)

## Task include
- [x] Trace producer/consumer app.
- [x] Trace ksqlDB/Kafka-Stream app.
- [ ] Trace Kafka Connect.
- [ ] End-to-end: API... Kafka... Python App... Stream App... Connect...
- [ ] Metrics API

## Setup steps

1. Download javaagent jar file.
   1. ```
      curl -o ./agents/opentelemetry-javaagent.jar https://github.com/open-telemetry/opentelemetry-java-instrumentation/releases/download/v1.14.0/opentelemetry-javaagent.jar
      ```
2. Bring services up.
   1. ```
      docker-compose up -d
      ```
3. Create ksqlDB pipelines (Uses Kafka-Stream)
   1. ```
      docker exec -it ksqldb-cli ksql http://ksqldb-server:8088
      ```
   2. ```
      create stream input_json (foo string) with (kafka_topic='converted', value_format='json');
      create stream converted_avro with (key_format='avro', value_format='avro') as select * from input_json;
      create table pv_count as select foo, as_value(foo) as url, as_value(windowstart) as st, as_value(windowend) as ed, count(*) as count from converted_avro window tumbling (size 1 minute) group by foo emit changes;
      ```
4. Setup Mysql
   1. ```
      docker exec -it mysql /bin/bash
      
      # password: mysql-pw
      mysql -u root -p
      
      GRANT ALL PRIVILEGES ON *.* TO 'example-user' WITH GRANT OPTION;
      ALTER USER 'example-user'@'%' IDENTIFIED WITH mysql_native_password BY 'example-pw';
      FLUSH PRIVILEGES;
      
      create table PV_COUNT(URL varchar(64) not null primary key);
      ```
5. Create Mongodb Sink
   1. ```
      -- This will re-use ksqlDB CLI.
      
      CREATE SINK CONNECTOR sink_result_to_db WITH (
      'connector.class'='io.confluent.connect.jdbc.JdbcSinkConnector',
      'connection.url'='jdbc:mysql://mysql:3306/example-db',
      'connection.user'='example-user',
      'connection.password'='example-pw',
      
      'key.converter'='org.apache.kafka.connect.storage.StringConverter',
      'key.converter.schema.registry.url' = 'http://schema-registry:8081',
      'value.converter'='io.confluent.connect.avro.AvroConverter',
      'value.converter.schema.registry.url' = 'http://schema-registry:8081',
      
      'insert.mode'='upsert',
      'pk.mode'='record_key',
      'pk.fields'='URL',
      'fields.whitelist'='URL,ED,ST,COUNT',
      'auto.create'='true',
      'auto.evolve'='true',
      'topics'='PV_COUNT'
      );
      ```
      
6. Access http://localhost:5001/ to trigger Kafka message write.
7. The message above will trigger downstream applications.

## Notes:

- Otel sends traces to `OTEL_EXPORTER_OTLP_ENDPOINT=localhost:4317` by default.
- Collector forwards traces to `OTEL_EXPORTER_JAEGER_ENDPOINT=localhost:14250` by default.
- Jaeger 6831 accepts trace directly.
- Jaeger 6831 port must be udp, `6831:6831/udp`

## References:

- https://opentelemetry.io/docs/instrumentation/python/getting-started/
- https://open-telemetry.github.io/
- https://docs.confluent.io/kafka-connect-jdbc/current/sink-connector/index.html