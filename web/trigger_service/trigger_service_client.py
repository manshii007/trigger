import grpc
import trigger_service.trigger_service_pb2_grpc as trigger_service_pb2_grpc
import trigger_service.trigger_service_pb2 as trigger_service_pb2


def guide_process_video(url):
    channel = grpc.insecure_channel('13.82.218.179:50051')
    stub = trigger_service_pb2_grpc.TriggerServiceStub(channel)
    video = trigger_service_pb2.Video()
    video.url = url
    return stub.GetTags(video)


def guide_process_video_compliance(url):
    channel = grpc.insecure_channel('13.82.218.179:50052')
    stub = trigger_service_pb2_grpc.TriggerServiceStub(channel)
    video = trigger_service_pb2.Video()
    video.url = url
    return stub.GetTags(video)


def guide_process_video_samosa(url):
    channel = grpc.insecure_channel('13.82.218.179:50052')
    stub = trigger_service_pb2_grpc.TriggerServiceStub(channel)
    video = trigger_service_pb2.Video()
    video.url = url
    return stub.GetTags(video)


if __name__ == '__main__':
    # tags = guide_process_video(
    #     'https://triggerbackendnormal.blob.core.windows.net/backend-media/videos/'
    #     'a23aa75a-6613-48ba-bbfa-cbe5b7e9ea4c.mp4')
    tags = guide_process_video('https://triggerbackendnormal.blob.core.windows.net/backend-media/'
                               'a1a7dda4-f0d8-4440-9047-7cfa8fe59625.mp4')
    bbox = {}
    for tag in tags:
        label = str(tag.labels)
        print(label)
        try :
            if bbox[label][-1][1] == (tag.start_frame -1):
                bbox[label][-1][1] = tag.end_frame
            else:
                bbox[label].append([tag.start_frame, tag.end_frame])
        except KeyError:
            bbox[label] = [[tag.start_frame, tag.end_frame]]
    print(bbox)


