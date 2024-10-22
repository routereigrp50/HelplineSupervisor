from handlers.logging import Logging as h_log
import functools
import time



def retry(retries):
    def decorator_retry_on_failure(func):
        @functools.wraps(func)
        def wrapper_retry_on_failure(*args, **kwargs):
            h_log.create_log(5, "decorators.retry", f"Function {func.__name__} was passed to retry wrapper")
            for retry_counter in range(1, retries + 1):
                h_log.create_log(5, "decorators.retry", f"Function {func.__name__}. Attempt {retry_counter} of {retries}")
                success, result = func(*args, **kwargs)
                if success:
                    h_log.create_log(5, "decorators.retry", f"Function {func.__name__}. Attempt {retry_counter} of {retries} was successful")
                    return (True, result)
                if retry_counter < retries:
                    delay = 10 * retry_counter
                    h_log.create_log(5, "decorators.retry", f"Function {func.__name__}. Attempt {retry_counter} of {retries} failed. Retrying in {delay} seconds")
                    time.sleep(delay)
            h_log.create_log(5, "decorators.retry", f"Function {func.__name__}. All {retries} attempts failed")
            return (False, result)
        return wrapper_retry_on_failure
    return decorator_retry_on_failure