from xbserver_plugin import IfmoXBServerConfiguration
from path import path


class ImageMagickConfiguration(IfmoXBServerConfiguration):

    TMP_PATH = '/tmp/xblock_imagemagick/'
    REPORT_PATH = "/tmp/xblock_imagemagick/reports"

    TIMEOUT_EXEC = path("/scilab/bin/timeout")
    DEFAULT_TIMEOUT = 10

    COMPARE_EXEC = path("compare")

    IDENTIFY_EXEC = path("identify")
    IDENTIFY_FORMAT = "%[fx:h*w]"

    CONVERT_EXEC = path("convert")

    DEFAULT_BASE_THRESHOLD = 50
    DEFAULT_SCALE_THRESHOLD = 80
    DEFAULT_QUALITY_FUZZ = 0
    DEFAULT_REPORT_SIZE = 400
