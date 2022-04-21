from scenedetect.video_manager import VideoManager
from scenedetect.scene_manager import SceneManager
from scenedetect.stats_manager import StatsManager
from scenedetect.detectors.content_detector import ContentDetector

def get_cuts(path, threshold=50, min_seconds=10):
    """Detects logical hardcuts in videos using pyscene detect

    Arguments:
        path (str): Local path for the video file

        threshold (int): Intensity value that triggers a cut

        min_seconds (int): Minimum seconds a cut should last

    Returns:
        LIST[TUPLE[INT]]: Returns a list of tuples containg start and end times for cuts
    """
    video_manager = VideoManager([path])
    stats_manager = StatsManager()
    scene_manager = SceneManager(stats_manager)
    min_scene_len = int(video_manager.get_framerate()) * min_seconds
    scene_manager.add_detector(ContentDetector(threshold=threshold, min_scene_len=min_scene_len))
    base_timecode = video_manager.get_base_timecode()
    video_manager.set_downscale_factor()

    video_manager.start()
    scene_manager.detect_scenes(frame_source=video_manager, show_progress=False)
    scene_list = scene_manager.get_scene_list(base_timecode)

    scene_list = [[x[0].get_seconds(), x[1].get_seconds()] for x in scene_list]

    return scene_list

