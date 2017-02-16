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
