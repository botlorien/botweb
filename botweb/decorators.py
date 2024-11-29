import logging
import time


def retry(
    time_out: int = 20,
    raise_exception: bool = True,
    show_exception: bool = False,
    delay: int = 1,
    **kwargsv
):
    def wrapper(func):
        def inner_wrapper(*args, **kwargs):
            contador_time_out = 0
            ret = (
                False
                if "default_return" not in kwargsv
                else kwargsv.pop("default_return")
            )
            error = None
            while contador_time_out < time_out:
                if "verbose" in kwargsv:
                    logging.info("#" * 20, func.__name__, "#" * 20)
                    logging.info("_" * 20, "args", "_" * 20)
                    logging.info(args)
                    logging.info("_" * 20, "kwargs", "_" * 20)
                    logging.info(kwargs)
                try:
                    ret = func(*args, **kwargs)
                    break
                except Exception as e:
                    error = e
                    if show_exception:
                        logging.exception(error)
                    time.sleep(delay)
                contador_time_out += 1

                if contador_time_out >= time_out and raise_exception:
                    raise error
            return ret

        return inner_wrapper

    return wrapper
