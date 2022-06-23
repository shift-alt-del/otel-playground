create stream s_input (url string) with (
 kafka_topic='async-queue-enriched', value_format='json');

create stream s_avro with (
 key_format='avro', value_format='avro') as select * from s_input;

create table t_pv_count as
select
 url,
 as_value(windowstart) as st,
 as_value(windowend) as ed,
 count(*) as count
from s_avro window tumbling (size 10 second)
group by url emit changes;

create stream s_pv_count with (kafka_topic='T_PV_COUNT', key_format='avro', value_format='avro');

create stream s_output as select rowkey, as_value(rowkey) url, st, ed, count from s_pv_count partition by rowkey;