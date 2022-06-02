import grpc
import logging
import time
from random import randint
from jaeger_client import Config
from grpc_opentracing import open_tracing_client_interceptor
from grpc_opentracing.grpcext import intercept_channel

from Jeager_Grpc import hello_pb2_grpc, hello_pb2

if __name__ == "__main__":
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
    tracing_interceptor = open_tracing_client_interceptor(tracer)

    with grpc.insecure_channel("localhost:50051") as channel:
        tracing_channel = intercept_channel(channel, tracing_interceptor)

        stub = hello_pb2_grpc.GreeterStub(tracing_channel)
        hello_request = hello_pb2.HelloRequest()
        hello_request.name = "tracydzf"
        rsp: hello_pb2.HelloReply = stub.SayHello(hello_request)

        print(rsp.message)

    time.sleep(
        2)  # yield to IOLoop to flush the spans - https://github.com/jaegertracing/jaeger-client-python/issues/50
    tracer.close()
