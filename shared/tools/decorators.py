import functools
import time



def retry(retries):
    def decorator_retry_on_failure(func):
        @functools.wraps(func)
        def wrapper_retry_on_failure(*args, **kwargs):
            for retry_counter in range(1, retries + 1):
                success, result = func(*args, **kwargs)
                if success:
                    return (True, result)
                if retry_counter < retries:
                    delay = 10 * retry_counter
                    time.sleep(delay)
            return (False, result)
        return wrapper_retry_on_failure
    return decorator_retry_on_failure