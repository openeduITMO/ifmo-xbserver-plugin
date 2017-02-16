# -*- coding=utf-8 -*-

import base64
import json
import logging
import os
import requests
import tempfile
import zipfile

from cStringIO import StringIO
from path import path

from xbserver_plugin import IfmoXBServerPlugin
from xqueue_api.xsubmission import XSubmission

from scilabserver_plugin.scilab_plugin_settings import *
from scilabserver_plugin.executable import spawn_scilab
from scilabserver_plugin.xqueue.xgeneration import XGeneration


class ScilabServerPlugin(IfmoXBServerPlugin):

    configuration_section = "ifmo_xblock_scilab"

    @IfmoXBServerPlugin.register_method("ScilabServerPlugin", "check")
    @IfmoXBServerPlugin.want_xobject(XSubmission)
    def do_check(self, xobject):

        xsubmission = xobject
        xsubmission.set_grade(grader=self.configuration.get('GRADER_ID'))

        result = {}

        # Dicts
        student_input = json.loads(xsubmission.student_response)
        grader_payload = json.loads(xsubmission.grader_payload)

        # Archives
        data = self.get_archives(student_input.get('archive_64_url'))

        student_filename, student_file = self.get_raw_archive(data, 'user_archive')
        instructor_filename, instructor_file = self.get_raw_archive(data, 'instructor_archive')

        # Полный рабочий путь в системе, со временной директорией, сразу вычистим
        TMP_PATH.makedirs_p()
        full_path = tempfile.mkdtemp(prefix=TMP_PATH)

        # Подчистка с самого начала нам не нужна, поскольку можно положиться на то,
        # что будет создан уникальный путь
        # cleanup(cwd=full_path)

        # Извлекаем архив студента
        try:
            student_archive = zipfile.ZipFile(student_file)
            student_archive.extractall(full_path)
        except (zipfile.BadZipfile, IOError):
            feedback = self.make_feedback(message='SAE: Не удалось открыть архив с ответом. '
                                                  'Загруженный файл должен быть .zip.',
                                          msg_type='error')
            return xsubmission.set_grade(feedback=feedback, success=False)

        # Процессу разрешено выполняться только 2 секунды
        filename = full_path / SCILAB_STUDENT_SCRIPT

        if os.path.exists(filename):

            # Допишем функцию выходна, на всякий случай
            with open(filename, "a") as source_file:
                source_file.write("exit();")

            student_code = spawn_scilab(filename, timeout=grader_payload.get('time_limit_execute') or DEFAULT_TIMEOUT)
            if student_code.get('return_code') == -1:
                feedback = self.make_feedback(message='TL: Превышен лимит времени', msg_type='error',
                                              pregenerated=grader_payload.get('pregenerated'),
                                              output_execute=student_code['output'])
                return xsubmission.set_grade(feedback=feedback, success=False)

        else:
            student_code = {
                'return_code': -2,
                'output': None,
            }
            logging.debug("No executable found in student answer (does not exists): %s" % filename)

        # Запишем pregenerated, если он вообще есть
        if grader_payload.get('pregenerated') is not None:
            with open(full_path / "generate_output", "w") as f:
                f.write(grader_payload['pregenerated'])

        try:
            instructor_archive = zipfile.ZipFile(instructor_file)
            instructor_archive.extractall(full_path)
        except (zipfile.BadZipfile, IOError):
            feedback = self.make_feedback(message='IAE: Не удалось открыть архив инструктора.', msg_type='error')
            return xsubmission.set_grade(feedback=feedback, success=False)

        filename = full_path / SCILAB_INSTRUCTOR_SCRIPT

        # Допишем функцию выхода, на всякий случай
        with open(filename, "a") as source_file:
            source_file.write("\nexit();\n")

        checker_code = spawn_scilab(filename, timeout=grader_payload.get('time_limit_check') or DEFAULT_TIMEOUT)
        if checker_code.get('return_code') == -1:
            feedback = self.make_feedback(message='TL: Превышен лимит времени', msg_type='error',
                                          pregenerated=grader_payload.get('pregenerated'),
                                          output_execute=student_code['output'],
                                          output_check=checker_code['output'])
            return xsubmission.set_grade(feedback=feedback, success=False)

        try:
            f = open(full_path / 'check_output')
            result_grade = float(f.readline().strip())
            result_message = f.readline().strip()
        except IOError:
            feedback = self.make_feedback(message='COE: Не удалось определить результат проверки.', msg_type='error',
                                          output_execute=student_code['output'],
                                          output_check=checker_code['output'])
            return xsubmission.set_grade(feedback=feedback, success=False)

        feedback = self.make_feedback(message=result_message, msg_type='success',
                                      pregenerated=grader_payload.get('pregenerated'),
                                      output_execute=student_code['output'],
                                      output_check=checker_code['output'])
        return xsubmission.set_grade(grade=result_grade, feedback=feedback, correctness=True, success=True)

    @IfmoXBServerPlugin.register_method("ScilabServerPlugin", "generate")
    @IfmoXBServerPlugin.want_xobject(XGeneration)
    def do_generate(self, xobject):

        xgeneration = xobject

        # Archives
        archives = self.get_archives(xgeneration.archive_url)
        instructor_filename, instructor_file = self.get_raw_archive(archives, 'instructor_archive')
        grader_payload = json.loads(xgeneration.grader_payload)

        # Полный рабочий путь в системе, со временной директорией, сразу вычистим
        # TODO: generate RANDOM path using guid
        TMP_PATH.makedirs_p()
        full_path = tempfile.mkdtemp(prefix=TMP_PATH)

        # Подчистка с самого начала нам не нужна, поскольку можно положиться на то,
        # что будет создан уникальный путь
        # cleanup(cwd=full_path)

        try:
            instructor_archive = zipfile.ZipFile(instructor_file)
            instructor_archive.extractall(full_path)
        except Exception:
            return xgeneration.set_generation_result(False, "Archive read/extract error")

        filename = full_path / SCILAB_GENERATE_SCRIPT

        # Допишем функцию выхода, на всякий случай
        with open(filename, "a") as source_file:
            source_file.write("\nexit();\n")

        generate_code = spawn_scilab(filename, timeout=grader_payload.get('time_limit_generate') or DEFAULT_TIMEOUT)

        try:
            with open(full_path + '/generate_output', 'r') as f:
                pregenerated = f.read()
        except IOError:
            return xgeneration.set_generation_result(False, "Pregenerated read error")

        xgeneration.set_generation_result(True, pregenerated)

        return xgeneration

    @classmethod
    def get_raw_archive(cls, data, archive):
        archive_path = path(data.get('%s_name' % archive))
        archive_raw = StringIO(base64.decodestring(data.get(archive)))
        return archive_path, archive_raw

    @classmethod
    def get_archives(cls, url):
        return json.loads(requests.get(url).text)

    @classmethod
    def make_feedback(cls, msg_type=None, message=None, output_execute=None, output_check=None, pregenerated=None):
        result = {}
        if msg_type is not None:
            result['msg_type'] = msg_type
        if message is not None:
            result['message'] = message
        if output_execute is not None:
            result['output_execute'] = unicode(output_execute, errors='replace')
        if output_check is not None:
            result['output_check'] = unicode(output_check, errors='replace')
        if pregenerated is not None:
            result['pregenerated'] = pregenerated
        return json.dumps(result)
