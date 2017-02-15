from path import path

TMP_PATH = path('/tmp/xblock_scilab/')

# Local ws03
SCILAB_EXEC = path("/opt/scilab-5.5.2/bin/scilab-adv-cli")
SCILAB_HOME = path("/opt/scilab-5.5.2/")

TIMEOUT_EXEC = path("/scilab/bin/timeout")

SCILAB_STUDENT_SCRIPT = "solution.sce"
SCILAB_INSTRUCTOR_SCRIPT = "check.sce"
SCILAB_GENERATE_SCRIPT = "generate.sce"
SCILAB_EXEC_SCRIPT = "disp('Execution started'); " \
                     "chdir('{pwd}'); " \
                     "exec('{filename}'); " \
                     "disp('Finish token: {token}'); " \
                     "exit();"

DEFAULT_TIMEOUT = 10
