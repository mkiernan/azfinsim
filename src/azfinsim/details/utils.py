import logging
import random

log = logging.getLogger(__name__)

def InjectRandomFail(failure):
    if random.uniform(0.0, 1.0) < failure:
       log.error("RANDOM ERROR INJECTION: TASK EXIT WITH ERROR")
       return True
    return False

def DoFakeCompute(xmlstring,delay_time,task_duration,mem_usage):
    import numpy as np
    import time
    import random
    # allocate the memory
    array_size = (mem_usage, 131072)
    data = np.ones(array_size, dtype=np.float64)
    # do startup delay
    time.sleep(delay_time)

    # now do fake computation
    task_duration_s = task_duration / 1000.0 #- convert from ms to s
    end_time = time.time() + task_duration_s
    while time.time() < end_time:
        data *= 12345.67890
        data[:] = 1.0
