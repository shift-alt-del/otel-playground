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
from s_avro window tumbling (size 10 second)
group by url emit changes;