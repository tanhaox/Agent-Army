from enum import Enum


class ProgressStep(str, Enum):
    FETCHING_PROFILE = "fetching_profile"
    FETCHING_VIDEO_LIST = "fetching_video_list"
    FILTERING_AND_SORTING = "filtering_and_sorting"
    TOP_SELECTED = "top_selected"
    DOWNLOADING_VIDEOS = "downloading_videos"
    EXTRACTING_AUDIO = "extracting_audio"
    TRANSCRIBING = "transcribing"
    SEARCH_ENHANCING = "search_enhancing"
    ANALYZING = "analyzing"
    GENERATING_REPORT = "generating_report"
    DONE = "done"
    ERROR = "error"
