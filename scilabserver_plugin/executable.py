# -*- coding=utf-8 -*-

import logging
import uuid
import os

from subprocess import Popen, PIPE
from scilab_server.executils import demote, read_all

from .scilab_plugin_settings import *

logger = logging.getLogger(__name__)


def spawn_scilab(filename, cwd=None, timeout=None, extra_env=None, use_display=False):
    """
    Запускает инстанс scilab'а с указанным файлом и параметрами. Возвращает
    результат выполнения.

    :param filename: Имя файла для исполнения
    :param cwd: Рабочая директория, по умолчанию является директориией, где
                располагается скрипт для исполнения
    :param timeout: Время на исполнение в секундах
    :param extra_env: Дополнительные переменные окружения
    :return: Результат выполнения
    """

    assert isinstance(filename, path)

    # Устанавливаем рабочую директорию, если необходимо
    if cwd is None:
        cwd = filename.dirname()
        logger.warning("No cwd specified for scilab_spawn, "
                       "default is used: %s", cwd)

    # Устанавливаем окружение
    env = os.environ.copy()
    env['SCIHOME'] = SCILAB_HOME

    if use_display is None:
        env['DISPLAY'] = ':99'
    elif isinstance(use_display, basestring):
        env['DISPLAY'] = use_display

    if isinstance(extra_env, dict):
        env.update(extra_env)

    # Для опредлеления того, завершился ли скрипт или ушёл в цикл скрипт,
    # будем мониторить вывод
    uid = str(uuid.uuid4())
    script = SCILAB_EXEC_SCRIPT.format(pwd=cwd, filename=filename, token=uid)

    # Запускаем процесс
    # TODO Найти, как запустить scilab без шелла
    # Если запускать его без шелла, то xcos не может отработать, поскольку
    # что-то ему не даёт подключиться к Xserver'у
    timeout_params = []
    if timeout:
        timeout_params += ['/ifmo/bin/timeout', '-t', str(timeout), '--detect-hangups']
    cmd = [SCILAB_EXEC, '-e', script, '-nb']
    if timeout_params:
        logger.info("Timeout params are used: {params}".format(params=timeout_params))
        cmd = timeout_params + cmd
    logger.info(" ".join([str(i) for i in cmd]))
    process = Popen(cmd,
                    cwd=cwd, env=env, stdout=PIPE, bufsize=1,  shell=False,
                    preexec_fn=demote())
    # set_non_block(process)

    # Убиваем по таймауту или ждём окончания исполнения, если он не задан
    if timeout is None:
        # Скорей всего, в этом случае произойдёт блокировка намертво,
        # поскольку scilab сам не завершится, поэтому timeout нужно задать
        logger.warning('Process timeout is not set. Now being in wait-state...')
        process.wait()
        output = read_all(process)
        return_code = process.returncode
    else:
        # time.sleep(timeout)
        # output = read_all(process)
        output, err_output = process.communicate()
        # os.killpg(process.pid, signal.SIGTERM)
        if output.find(uid) != -1:
            return_code = 0
        else:
            return_code = -1

    logger.debug(output)

    # Возвращаем результат исполнения
    return {
        'code': return_code,
        'output': output,
        'error': err_output
    }
