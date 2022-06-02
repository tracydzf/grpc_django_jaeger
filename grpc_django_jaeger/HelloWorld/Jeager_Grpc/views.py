import grpc
import requests
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
import time
import grpc
from django.conf import settings
from grpc_opentracing.grpcext import intercept_channel
from Jeager_Grpc import hello_pb2_grpc, hello_pb2
from grpc_opentracing import open_tracing_server_interceptor, open_tracing_client_interceptor
# # Create your views here.
# from opentelemetry import trace
# from opentelemetry.sdk.trace import TracerProvider
# from opentelemetry.sdk.trace.export import (
#     ConsoleSpanExporter,
#     SimpleExportSpanProcessor,
# )
# trace.get_tracer_provider().add_span_processor(
#     SimpleExportSpanProcessor(ConsoleSpanExporter())
# )
from jaeger_client import Config

# this call also sets opentracing.tracer

config = Config(config=settings.OPENTRACING_TRACER_CONFIG, service_name="Jeager_Grpc", validate=True)
tracer = config.initialize_tracer()


class DefaultInterceptors(grpc.UnaryUnaryClientInterceptor):
    def intercept_unary_unary(self, continuation, client_call_details, request):
        from datetime import datetime
        start = datetime.now()
        resp = continuation(client_call_details, request)
        print((datetime.now() - start).microseconds / 1000)
        return resp


def test1(request):
    with tracer.start_span("spider") as spider_span:
        req = requests.get("https://www.baidu.com")
        time.sleep(
            1)  # yield to IOLoop to flush the spans - https://github.com/jaegertracing/jaeger-client-python/issues/50

    tracer_interceptor = open_tracing_client_interceptor(tracer)
    default_interceptor = DefaultInterceptors()
    with grpc.insecure_channel("localhost:50051") as channel:
        try:
            old_intercept_channel = grpc.intercept_channel(channel, default_interceptor)

            trace_intercept_channel = intercept_channel(old_intercept_channel, tracer_interceptor)
            stub = hello_pb2_grpc.GreeterStub(trace_intercept_channel)
            hello_request = hello_pb2.HelloRequest()
            hello_request.name = "tracydzf"
            rsp: hello_pb2.HelloReply = stub.SayHello(hello_request)

            print(rsp.message)

        except grpc.RpcError as e:
            err_msg = "stream call err, code: %s, msg: %s" % (e.code(), e.details())
            print(err_msg)

    time.sleep(
        2)  # yield to IOLoop to flush the spans - https://github.com/jaegertracing/jaeger-client-python/issues/50

    return HttpResponse("sb")
