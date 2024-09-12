import functools
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class ErrorHandler(object):
    def __init__(self, default_error_message=">>AUTHz ERROR"):
        self.default_error_message = default_error_message
        self.error_codes = {
            100: ">>LOGIN FAILED",
            101: ">>RECOVERY FAILED",
            102: ">>USER NOT FOUND",
            103: ">>SERVICE NOT FOUND",
            104: ">>INVALID SEED > DELETED SERVICE",
            105: ">>INVALID SEED",
            106: ">>INVALID TYPE",
            107: ">>SERVICE ALREADY EXISTS",
            108: ">>PASSWORDS DO NOT MATCH",
        }

    def __call__(self, func):
        @functools.wraps(func)
        def wrapper(instance, *args, **kwargs):
            try:
                if hasattr(instance, "login_state"):
                    if (
                        instance.login_state == "register"
                        and func.__name__ != "register"
                    ):
                        print(">>USER NOT REGISTERED")
                        return self.default_error_message
                return func(instance, *args, **kwargs)
            except Exception as e:
                if e.args:
                    error_code = e.args[0]
                    if error_code in self.error_codes:
                        print(self.error_codes[error_code])
                        return
                logging.error(e)
                return self.default_error_message

        return wrapper
