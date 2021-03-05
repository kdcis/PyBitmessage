"""
Common reusable code for tests and tests for pybitmessage process.
"""

import os
import signal
import subprocess  # nosec
import sys
import state
import tempfile
import time
import unittest

import psutil

from .common_data import cleanup, put_signal_file, skip_python3

skip_python3()


class TestProcessProto(unittest.TestCase):
    """Test case implementing common logic for external testing:
    it starts pybitmessage in setUpClass() and stops it in tearDownClass()
    """
    _process_cmd = ['pybitmessage', '-d']
    _threads_count_min = 15
    _threads_count_max = 16
    _threads_names = [
        'PyBitmessage',
        'addressGenerato',
        'singleWorker',
        'SQL',
        'objectProcessor',
        'singleCleaner',
        'singleAPI',
        'Asyncore',
        'ReceiveQueue_0',
        'ReceiveQueue_1',
        'ReceiveQueue_2',
        'Announcer',
        'InvBroadcaster',
        'AddrBroadcaster',
        'Downloader',
        'Uploader'
    ]
    _files = (
        'keys.dat', 'debug.log', 'messages.dat', 'knownnodes.dat',
        '.api_started', 'unittest.lock'
    )
    home = None

    @classmethod
    def setUpClass(cls):
        """Setup environment and start pybitmessage"""
        print('setUpClass.........................................(pass)', state.appdata)
        # print('os.environ["BITMESSAGE_HOME"](test_process file)57...........................', os.environ['BITMESSAGE_HOME'])
        print(__file__, 'cls.home..................................', cls.home)
        cls.flag = False
        # if os.environ.get('BITMESSAGE_HOME'):
        #     cls._cleanup_files()
        #     cls.home = os.environ.get('BITMESSAGE_HOME')
        # else:
        #     if not cls.home:
        #         cls.home = tempfile.gettempdir()
        #         cls._cleanup_files()
        #     os.environ['BITMESSAGE_HOME'] = cls.home
        cls.flag = False
        if not cls.home:
            cls.home = tempfile.gettempdir()
            cls._cleanup_files()
        os.environ['BITMESSAGE_HOME'] = cls.home

        print('os.environ["BITMESSAGE_HOME"](test_process file)65...........................', os.environ['BITMESSAGE_HOME'])
        put_signal_file(cls.home, 'unittest.lock')
        starttime = int(time.time()) - 0.5
        cls.process = psutil.Popen(
            cls._process_cmd, stderr=subprocess.STDOUT)  # nosec

        pidfile = os.path.join(cls.home, 'singleton.lock')
        for _ in range(10):
            time.sleep(1)
            try:
                pstat = os.stat(pidfile)
                if starttime <= pstat.st_mtime and pstat.st_size > 0:
                    break  # the pidfile is suitable
            except OSError:
                continue

        try:
            pid = int(cls._get_readline('singleton.lock'))
            cls.process = psutil.Process(pid)
            time.sleep(5)
        except (psutil.NoSuchProcess, TypeError):
            cls.flag = True

    def setUp(self):
        print('setUp.........................................(pass)')
        if self.flag:
            self.fail("%s is not started ):" % self._process_cmd)

    @classmethod
    def _get_readline(cls, pfile):
        print('_get_readline.........................................(pass)')
        pfile = os.path.join(cls.home, pfile)
        try:
            return open(pfile, 'rb').readline().strip()
        except (OSError, IOError):
            pass

    @classmethod
    def _stop_process(cls, timeout=5):
        print('_stop_process.........................................(pass)')
        cls.process.send_signal(signal.SIGTERM)
        try:
            cls.process.wait(timeout)
        except psutil.TimeoutExpired:
            return False
        return True

    @classmethod
    def _kill_process(cls, timeout=5):
        print('_kill_process.........................................')
        try:
            cls.process.send_signal(signal.SIGKILL)
            cls.process.wait(timeout)
        # Windows or already dead
        except (AttributeError, psutil.NoSuchProcess):
            return True
        # except psutil.TimeoutExpired propagates, it means something is very
        # wrong
        return True

    @classmethod
    def _cleanup_files(cls):
        print('_cleanup_files.........................................(pass)')
        cleanup(cls.home, cls._files)

    @classmethod
    def tearDownClass(cls):
        """Ensures that pybitmessage stopped and removes files"""
        print('tearDownClass.........................................(pass)')
        try:
            if not cls._stop_process(10):
                processes = cls.process.children(recursive=True)
                processes.append(cls.process)
                for p in processes:
                    try:
                        p.kill()
                    except psutil.NoSuchProcess:
                        pass
        except psutil.NoSuchProcess:
            pass
        finally:
            cls._cleanup_files()

    def _test_threads(self):
        """Test number and names of threads"""

        # pylint: disable=invalid-name
        print('_test_threads.........................................(pass)')
        self.longMessage = True

        try:
            # using ps for posix platforms
            # because of https://github.com/giampaolo/psutil/issues/613
            thread_names = subprocess.check_output([
                "ps", "-L", "-o", "comm=", "--pid",
                str(self.process.pid)
            ]).split()
        except:  # pylint: disable=bare-except
            thread_names = []

        running_threads = len(thread_names)
        if 0 < running_threads < 30:  # adequacy check
            extra_threads = []
            missing_threads = []
            for thread_name in thread_names:
                if thread_name not in self._threads_names:
                    extra_threads.append(thread_name)
            for thread_name in self._threads_names:
                if thread_name not in thread_names:
                    missing_threads.append(thread_name)

            msg = "Missing threads: {}, Extra threads: {}".format(
                ",".join(missing_threads), ",".join(extra_threads))
        else:
            running_threads = self.process.num_threads()
            if sys.platform.startswith('win'):
                running_threads -= 1  # one extra thread on Windows!
            msg = "Unexpected running thread count"

        self.assertGreaterEqual(
            running_threads,
            self._threads_count_min,
            msg)

        self.assertLessEqual(
            running_threads,
            self._threads_count_max,
            msg)

    def remove_temp_data(self):
        cleanup()
