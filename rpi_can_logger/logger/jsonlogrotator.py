import json

from datetime import datetime
import subprocess
from pathlib import Path
import logging
from io import StringIO
import random
import os
import string
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
        self._out_fh = os.open(self.log_folder + '/' + now.strftime('%Y%m%d_%H%M%S_{}.json'.format(self.make_random(6))),
                               mode=os.O_EXLOCK | os.O_WRONLY)
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
