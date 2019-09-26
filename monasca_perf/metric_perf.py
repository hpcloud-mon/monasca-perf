import datetime
import sys
import time
import multiprocessing

from keystoneauth1 import identity
from keystoneauth1 import session
from monascaclient import client

from agent_sim import agent_sim_process

import warnings

# suppress warnings to improve performance
def no_warnings(message, category, filename, lineno):
    pass
warnings.showwarning = no_warnings

num_processes = 10
num_requests = 4
num_metrics = 100

max_wait_time = 20  # Seconds
DISTINCT_METRICS = 20

keystone = {
    'username': 'mini-mon',
    'password': 'password',
    'project': 'mini-mon',
    #'auth_url': 'http://10.22.156.20:35358/v3',
    'auth_url': 'http://44.71.0.47/identity'
}

# monasca api urls
urls = [
    #'https://mon-ae1test-monasca01.useast.hpcloud.net:8080/v2.0',
    #'https://mon-ae1test-monasca02.useast.hpcloud.net:8080/v2.0',
    #'https://mon-ae1test-monasca03.useast.hpcloud.net:8080/v2.0',
    'http://44.71.0.47/metrics/v2.0',
]

if len(sys.argv) >= 2:
    num_processes = int(sys.argv[1])

total_metrics = num_processes*num_requests*num_metrics

class MetricCreatorMetricPerf():
    """ Generates metrics
    """
    def __init__(self, proc_num):
        self.proc_num = proc_num
        self.num_calls = 0

    def create_metric(self):
        metric = {"name": "metric_perf",
                  "dimensions": {"dim1": "agent-" + str(self.proc_num)},
                  "timestamp": time.time()*1000 + (self.num_calls % 1000), # timestamp must be unique
                  "value": 0}
        self.num_calls += 1
        return metric


def aggregate_sent_metric_count(sent_q):
    total_sent = 0
    while not sent_q.empty():
        item = sent_q.get()
        if isinstance(item,int):
            total_sent += item
        else:
            print(item)
    return total_sent


def metric_performance_test():

    auth = identity.Password(
        auth_url=keystone['auth_url'],
        username=keystone['username'],
        password=keystone['password'],
        project_name=keystone['project'],
        user_domain_id='default',
        project_domain_id='default'
    )
    sess = session.Session(auth=auth)

    mon_client = client.Client('2_0', urls[0], session=sess)

    sent_q = multiprocessing.Queue()

    process_list = []
    for i in xrange(num_processes):
        p = multiprocessing.Process(target=agent_sim_process(i, num_requests, num_metrics, urls[(i % len(urls))],
                                                             keystone, queue=sent_q,
                                                             metric_creator=MetricCreatorMetricPerf,
                                                             token=sess).run)
        process_list.append(p)

    start_datetime = datetime.datetime.now()
    start_datetime = start_datetime - datetime.timedelta(microseconds=start_datetime.microsecond)
    print("Starting test at: " + start_datetime.isoformat())
    start_time = time.time()

    for p in process_list:
        p.start()

    try:
        for p in process_list:
            try:
                p.join()
            except Exception:
                pass

    except KeyboardInterrupt:
        return False, "User interrupt"



    total_metrics_sent = aggregate_sent_metric_count(sent_q)

    metrics_found = 0
    last_count = 0
    last_change = time.time()
    while metrics_found < total_metrics_sent:

        metrics_found = 0
        try:
            stats = mon_client.metrics.list_statistics(statistics="count",
                                                       start_time=start_datetime.isoformat(),
                                                       name="metric_perf",
                                                       merge_metrics=True)
            metrics_found = stats[0]['statistics'][0][1]
        except Exception as ex:
            print("Failed to retrieve metrics from api\n{}".format(ex))

        if metrics_found > last_count:
            last_change = time.time()
            last_count = metrics_found

        if (last_change + max_wait_time) <= time.time():
            return False, "Max wait time exceeded, {0} / {1} metrics found".format(metrics_found, total_metrics_sent)
        time.sleep(1)

    final_time = time.time()
    print("-----Test Results-----")
    print("{} metrics in {} seconds".format(metrics_found, final_time-start_time))
    print("{} per second".format(metrics_found / (final_time - start_time)))

    return True, ""


def main():
    success, msg = metric_performance_test()
    if not success:
        print("-----Test failed to complete-----")
        print(msg)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
