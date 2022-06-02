import logging
import time
from concurrent import futures
from random import randint

import grpc
import opentracing
from django.conf import settings
from grpc_opentracing.grpcext import intercept_server
from Jeager_Grpc import hello_pb2_grpc, hello_pb2
from grpc_opentracing import open_tracing_server_interceptor

from jaeger_client import Config

log_level = logging.DEBUG
logging.getLogger('').handlers = []
logging.basicConfig(format='%(asctime)s %(message)s', level=log_level)

config = Config(config={
    'sampler': {
        'type': 'const',
        'param': 1,
    },
    'local_agent': {
        'reporting_host': 'localhost',
        'reporting_port': '6831',
    },
    'logging': True,
}, service_name="Jeager_Grpc_HelloServer", validate=True)
tracer = config.initialize_tracer()


#

class Greeter(hello_pb2_grpc.GreeterServicer):
    def SayHello(self, request, context):
        # 如何在这里找到父的span
        tracer1 = opentracing.global_tracer()
        with tracer1.start_span('execute', child_of=context.get_active_span()) as execute_span:
            time.sleep(randint(1, 9) * 0.1)
        return hello_pb2.HelloReply(message='Hello, %s!' % request.name)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    tracing_interceptor = open_tracing_server_interceptor(tracer)
    server = intercept_server(server, tracing_interceptor)

    hello_pb2_grpc.add_GreeterServicer_to_server(Greeter(), server)
    server.add_insecure_port('[::]:50051')
    server.start()

    _ONE_DAY_IN_SECONDS = 60 * 60 * 24
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)
    tracer.close()


if __name__ == '__main__':
    logging.basicConfig()
    serve()
