#!/usr/bin/env python

# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import multiprocessing as mp
import os
import pytest

from google.api_core.exceptions import AlreadyExists
from google.cloud import pubsub_v1

import sub


PROJECT = os.environ['GCLOUD_PROJECT']
TOPIC = 'quickstart-sub-test-topic'
SUBSCRIPTION = 'quickstart-sub-test-topic-sub'

publisher_client = pubsub_v1.PublisherClient()
subscriber_client = pubsub_v1.SubscriberClient()


@pytest.fixture(scope='module')
def topic_path():
    topic_path = publisher_client.topic_path(PROJECT, TOPIC)

    try:
        topic = publisher_client.create_topic(topic_path)
        return topic.name
    except AlreadyExists:
        return topic_path


@pytest.fixture(scope='module')
def subscription_path(topic_path):
    subscription_path = subscriber_client.subscription_path(
        PROJECT, SUBSCRIPTION)

    try:
        subscription = subscriber_client.create_subscription(
            subscription_path, topic_path)
        return subscription.name
    except AlreadyExists:
        return subscription_path


def _to_delete(resource_paths):
    for item in resource_paths:
        if 'topics' in item:
            publisher_client.delete_topic(item)
        if 'subscriptions' in item:
            subscriber_client.delete_subscription(item)


@pytest.fixture(scope='module')
def test_sub(topic_path, subscription_path, capsys):
    publish_future = publisher_client.publish(topic_path, data=b'Hello World!')
    publish_future.result()

    subscribe_process = mp.Process(
        target=sub.sub, args=(PROJECT, SUBSCRIPTION,))
    subscribe_process.start()
    subscribe_process.join(timeout=10)
    subscribe_process.terminate()

    # Clean up resources.
    _to_delete([topic_path, subscription_path])

    out, _ = capsys.readouterr()
    assert "Received message" in out
    assert "Acknowledged message" in out
