from django.conf import settings

from HelloWorld import after_request_trace, before_request_trace

try:
    # Django >= 1.10
    from django.utils.deprecation import MiddlewareMixin
except ImportError:
    MiddlewareMixin = object


# coding: utf-8

import six

from jaeger_client import Config

# Name of the HTTP header used to encode trace ID
DEFAULT_TRACE_ID_HEADER = 'trace_id' if six.PY3 else b'trace_id'


def init_tracer(service_name: str, config: dict):
    """
    initialize the global tracer
    :param service_name:
    :param config:
    :return:
    """
    assert isinstance(config, dict)
    # default use `trace_id` replace jaeger `uber-trace-id`
    config['trace_id_header'] = config.get('trace_id_header',
                                           DEFAULT_TRACE_ID_HEADER)

    config = Config(config=config, service_name=service_name, validate=True)
    import opentracing.tracer
    if config.initialized():
        tracer = opentracing.tracer
    else:
        tracer = config.initialize_tracer()
    return tracer


class OpenTracingMiddleware(MiddlewareMixin):
    def __init__(self, get_response=None):
        """
         __init__() is only called once, no arguments, when the Web server
        responds to the first request
        """
        self._init_tracer()
        self.get_response = get_response

    def _init_tracer(self):
        """
        get global tracer callable function from Django settings.
        :return:
        """
        assert settings.SERVICE_NAME
        assert settings.OPENTRACING_TRACER_CONFIG

        self.tracer = init_tracer(settings.SERVICE_NAME,
                                  settings.OPENTRACING_TRACER_CONFIG)

    def process_view(self, request, view_func, view_args, view_kwargs):
        print("!!!!!!!")
        print(self.tracer)
        before_request_trace(self.tracer, request, view_func)

    def process_exception(self, request, exception):
        after_request_trace(request, error=exception)

    def process_response(self, request, response):
        after_request_trace(request, response=response)
        return response
