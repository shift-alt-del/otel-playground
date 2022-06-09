from kafka import KafkaAdminClient
from kafka.admin import NewTopic


def create_topic_if_not_exist(conf, topic_name, default_partition=1, default_replication=1):
    try:
        KafkaAdminClient(**conf).create_topics([NewTopic(topic_name, default_partition, default_replication)])
    except:
        pass
