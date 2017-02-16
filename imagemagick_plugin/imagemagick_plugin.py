# -*- coding=utf-8 -*-

import json
import logging
import os
import requests
import tempfile
import uuid

from base64 import decodestring
from path import path
from subprocess import Popen, PIPE
from scilab_server.executils import demote
from xbserver_plugin import IfmoXBServerPlugin
from xqueue_api.xsubmission import XSubmission

from .imagemagick_settings import ImageMagickConfiguration


logger = logging.getLogger(__name__)


@IfmoXBServerPlugin.register_default_config(ImageMagickConfiguration)
class ImageMagickServerPlugin(IfmoXBServerPlugin):

    configuration_section = "ifmo_xblock_imagemagick"

    @IfmoXBServerPlugin.register_method("check")
    @IfmoXBServerPlugin.want_xobject(XSubmission)
    def check(self, xobject):

        # Инициализация
        student_input = json.loads(xobject.student_response)
        grader_payload = json.loads(xobject.grader_payload)

        # Сохраныем картинки во временной директории
        data = self.get_images(student_input.get('image_64_url'))

        student_filename, student_file = self.get_raw_image(data, 'user_image')
        instructor_filename, instructor_file = self.get_raw_image(data, 'instructor_image')

        temp_path = tempfile.mkdtemp(prefix=self.configuration.TMP_PATH.makedirs_p())

        student_fd, student_fullname = tempfile.mkstemp(dir=temp_path)
        with open(student_fullname, "wb") as f:
            f.write(student_file)

        instructor_fd, instructor_fullname = tempfile.mkstemp(dir=temp_path)
        with open(instructor_fullname, "wb") as f:
            f.write(instructor_file)

        self.configuration.REPORT_PATH.makedirs_p()
        report_filename = "%s.png" % str(uuid.uuid4())
        report_fullname = self.configuration.REPORT_PATH / report_filename

        # Подсчитаем размер изображения в пикселах
        identify_cmd = [self.configuration.IDENTIFY_EXEC, "-format", self.configuration.IDENTIFY_FORMAT, instructor_fullname]
        identify_result = self.spawn_compare(identify_cmd)
        total_size = float(identify_result["output"])

        # Запуск compare
        compare_cmd = [self.configuration.COMPARE_EXEC, student_fullname, instructor_fullname, report_fullname]

        if grader_payload.get("allowable_fuzz"):
            compare_cmd[1:1] = ["-fuzz", str(grader_payload.get("allowable_fuzz"))+"%", "-metric", "ae"]

        compare_result = self.spawn_compare(compare_cmd)

        if compare_result["code"] in [0, 1]:

            correct = (int(compare_result["err_output"]) / total_size * 100) <= grader_payload.get("cut_off", 0)
            feedback = self.make_feedback(output=compare_result["output"], err_output=compare_result["err_output"],
                                          report_file=report_filename)

            if correct:
                xobject.set_grade(feedback=feedback, grade=1, success=True, correctness=True)
            else:
                xobject.set_grade(feedback=feedback, grade=0, success=True, correctness=False)

        else:
            feedback = self.make_feedback(output=compare_result["output"], err_output=compare_result["err_output"])
            xobject.set_grade(feedback=feedback)

        return xobject

    @staticmethod
    def get_images(url):
        return json.loads(requests.get(url).text)

    @staticmethod
    def get_raw_image(data, archive):
        archive_path = path(data.get('%s_name' % archive))
        archive_raw = decodestring(data.get(archive))
        return archive_path, archive_raw

    @staticmethod
    def spawn_compare(cmd, cwd=None, timeout=None, extra_env=None, use_display=False):

        env = os.environ.copy()
        if extra_env is not None:
            env.update(extra_env)

        logger.info(" ".join([str(i) for i in cmd]))

        process = Popen(cmd, cwd=cwd, env=env, stdout=PIPE, stderr=PIPE, bufsize=1,  shell=False, preexec_fn=demote())
        output, err_output = process.communicate()

        return {
            "code": process.returncode,
            "output": output,
            "err_output": err_output,
        }

    @staticmethod
    def make_feedback(msg_type=None, message=None, output=None, err_output=None, report_file=None):
        result = {}
        if msg_type is not None:
            result['msg_type'] = msg_type
        if message is not None:
            result['message'] = message
        if output is not None:
            result['output'] = unicode(output, errors='replace')
        if err_output is not None:
            result['err_output'] = unicode(err_output, errors='replace')
        if report_file is not None:
            result['report_file'] = report_file
        return json.dumps(result)
