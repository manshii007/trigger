import grpc
from grpc.framework.common import cardinality
from grpc.framework.interfaces.face import utilities as face_utilities

import sys
import trigger_service.trigger_service_pb2 as trigger__service__pb2
import trigger_service.trigger_service_pb2 as trigger__service__pb2


class TriggerServiceStub(object):

  def __init__(self, channel):
    """Constructor.

    Args:
      channel: A grpc.Channel.
    """
    self.GetTags = channel.unary_stream(
        '/TriggerService/GetTags',
        request_serializer=trigger__service__pb2.Video.SerializeToString,
        response_deserializer=trigger__service__pb2.Tag.FromString,
        )


class TriggerServiceServicer(object):

  def GetTags(self, request, context):
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')


def add_TriggerServiceServicer_to_server(servicer, server):
  rpc_method_handlers = {
      'GetTags': grpc.unary_stream_rpc_method_handler(
          servicer.GetTags,
          request_deserializer=trigger__service__pb2.Video.FromString,
          response_serializer=trigger__service__pb2.Tag.SerializeToString,
      ),
  }
  generic_handler = grpc.method_handlers_generic_handler(
      'TriggerService', rpc_method_handlers)
  server.add_generic_rpc_handlers((generic_handler,))
