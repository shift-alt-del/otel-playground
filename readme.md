# Otel Playground

What to play

- Run python code and see Jaeger UI on http://localhost:16686/

Setup
```
create stream pv (foo string) with (kafka_topic='converted', value_format='json');
create table pv_count as select foo as url, count(*) as count from pv window tumbling (size 1 minute) group by foo emit changes;
```

Notes:

- Otel sends traces to `OTEL_EXPORTER_OTLP_ENDPOINT=localhost:4317` by default.
- Collector forwards traces to `OTEL_EXPORTER_JAEGER_ENDPOINT=localhost:14250` by default.
- Jaeger 6831 accepts trace directly.
- Jaeger 6831 port must be udp, `6831:6831/udp`

References:

- https://opentelemetry.io/docs/instrumentation/python/getting-started/