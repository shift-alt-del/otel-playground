# Otel Playground

## How to play
- API Service -> Kafka -> Apps -> KafkaStreams End-To-End distributed tracing.
- Access http://localhost:5001 to trigger kafka write.
- Access http://localhost:16686 to play with tracings on Jaeger UI.

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
      create stream converted (foo string) with (kafka_topic='converted', value_format='json');
      create table pv_count as select foo, count(*) as count from converted window tumbling (size 1 minute) group by foo emit changes;
      create stream filter1 as select * from converted where foo <> 'xxx';
      create stream filter2 as select * from filter1 where foo <> 'xxx';
      ```
      
4. Access http://localhost:5001/ to trigger Kafka message write.
5. The message above will trigger downstream applications.

## Notes:

- Otel sends traces to `OTEL_EXPORTER_OTLP_ENDPOINT=localhost:4317` by default.
- Collector forwards traces to `OTEL_EXPORTER_JAEGER_ENDPOINT=localhost:14250` by default.
- Jaeger 6831 accepts trace directly.
- Jaeger 6831 port must be udp, `6831:6831/udp`

## References:

- https://opentelemetry.io/docs/instrumentation/python/getting-started/