# Otel Playground

## What's this repo about

- [x] Trace producer/consumer app.
- [x] Trace ksqlDB/Kafka-Stream app.
- [ ] Trace Kafka Connect.
- [ ] End-to-end: API... Kafka... Python App... KsqlDB... Connect...
- [ ] Metrics API

Trace API writes Kafka.
![TraceOnline](images/trace_online.png)

Trace Kafka down stream microservices.
![TraceOffline](images/trace_offline.png)

## Environment setup

1. Download javaagent jar file.
   1. ```
      curl -o ./agents/opentelemetry-javaagent.jar https://github.com/open-telemetry/opentelemetry-java-instrumentation/releases/download/v1.14.0/opentelemetry-javaagent.jar
      ```

## Service startup
1. Bring services up.
    1. ```
       docker-compose up -d
       ```

2. Setup Mysql
    1. ```
       docker exec -it mysql mysql -uroot -pmysql-pw
       ```
    2. ```
       GRANT ALL PRIVILEGES ON *.* TO 'example-user' WITH GRANT OPTION;
       ALTER USER 'example-user'@'%' IDENTIFIED WITH mysql_native_password BY 'example-pw';
       FLUSH PRIVILEGES;
       ``` 
    3. ```
       use example-db;
       create table T_PV_COUNT(URL varchar(64) not null primary key);
       ```

3. Create ksqlDB pipelines
    1. ```
       docker exec -it ksqldb-cli ksql http://ksqldb-server:8088
       ```
    2. ```
       create stream s_input (url string) with (
         kafka_topic='async-queue-enriched', value_format='json');
      
       create stream s_avro with (
         key_format='avro', value_format='avro') as select * from s_input;
      
       create table t_pv_count as 
       select 
         url,
         latest_by_offset(url) as url_txt,
         as_value(windowstart) as st, 
         as_value(windowend) as ed, 
         count(*) as count 
       from s_avro window tumbling (size 1 minute) 
       group by url emit changes;
       ```

4. Create Mongodb Sink. 
   1. ```
      docker exec -it ksqldb-cli ksql http://ksqldb-server:8088
      ```
   2. ```
      CREATE SINK CONNECTOR sink_result_to_db WITH (
      'connector.class'='io.confluent.connect.jdbc.JdbcSinkConnector',
      'connection.url'='jdbc:mysql://mysql:3306/example-db',
      'connection.user'='example-user',
      'connection.password'='example-pw',
       
      'key.converter'='org.apache.kafka.connect.storage.StringConverter',
      'key.converter.schema.registry.url' = 'http://schema-registry:8081',
      'value.converter'='io.confluent.connect.avro.AvroConverter',
      'value.converter.schema.registry.url' = 'http://schema-registry:8081',
      'topics'='T_PV_COUNT',
       
      'insert.mode'='upsert',
      'fields.whitelist'='URL,URL_TXT,ED,ST,COUNT',
      'pk.mode'='record_key',
      'pk.fields'='URL',
      'auto.create'='true',
      'auto.evolve'='true'
      );
      ```

7. Access http://localhost:5001/ to trigger Kafka message write.
8. Access http://localhost:16686/ to view traces.

## Notes:

- Otel sends traces to `OTEL_EXPORTER_OTLP_ENDPOINT=localhost:4317` by default.
- Collector forwards traces to `OTEL_EXPORTER_JAEGER_ENDPOINT=localhost:14250` by default.
- Jaeger 6831 accepts trace directly.
- Jaeger 6831 port must be udp, `6831:6831/udp`

## References:

- https://opentelemetry.io/docs/instrumentation/python/getting-started/
- https://open-telemetry.github.io/
- https://docs.confluent.io/kafka-connect-jdbc/current/sink-connector/index.html