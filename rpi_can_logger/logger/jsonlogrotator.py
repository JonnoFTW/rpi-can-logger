from datetime import datetime
from pathlib import Path
from io import StringIO
import subprocess
import logging
import random
import string
import json
from .BaseLogRotator import BaseLogRotator


class JSONLogRotator(BaseLogRotator):
    """
    A JSON Log Rotator
    """

    def _make_writer(self):
        """

        :return:
        """
        self._buffer = StringIO()

        self._bytes_written = 0
        now = datetime.now()
        self.fname = self.log_folder + '/' + now.strftime('%Y%m%d_%H%M%S_{}.json'.format(self.make_random(6)))
        self._out_fh = open(self.fname, 'w')
        with open(self.pid_file, 'w') as pid_out:
            pid_out.write(self.fname)
        logging.warning("Writing to {} ({} bytes)".format(self._out_fh.name, self.max_bytes))

    @staticmethod
    def make_random(nchars):
        alphabet = string.ascii_letters + string.digits
        return ''.join(random.choice(alphabet) for _ in range(nchars))

    def close(self):
        self._out_fh.close()

    def writerow(self, row):
        """

        :param row:
        :return:
        """
        out_txt = json.dumps(row)+"\n"
        self._bytes_written += self._out_fh.write(out_txt)
        self._out_fh.flush()
        if self._bytes_written > self.max_bytes:
            self.close()
            out_name = str(Path(self._out_fh.name).absolute())
            subprocess.Popen(['7z', 'a', '-t7z', '-m0=lzma', '-mx=9', '-mfb=64', '-md=16m',
                              out_name + '.7z', out_name])
            self._make_writer()

        return out_txt
