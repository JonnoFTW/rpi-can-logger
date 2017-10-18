from datetime import datetime
from io import StringIO
import pathlib
from glob import glob
import logging
import random
import string
import json
import gzip
import shutil
import os
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
        self.fname = str(pathlib.Path(self.fname))
        self._out_fh = open(self.fname, 'w')
        self.write_pid()
        logging.warning("Writing to  {} ({} bytes)".format(self._out_fh.name, self.max_bytes))

        # compress any old files still lying around
        for fname in glob(self.log_folder+"/*.json"):
            if fname != self.fname:
                self._compress(fname)

    def write_pid(self):
        with open(self.pid_file, 'w') as pid_out:
            pid_out.write(self.fname)

    @staticmethod
    def make_random(nchars):
        alphabet = string.ascii_letters + string.digits
        return ''.join(random.choice(alphabet) for _ in range(nchars))

    def close(self):
        self._out_fh.close()

    def _compress(self, fname):
        try:
            with open(fname, 'rb') as f_in:
                logging.warning("Compressing {0} into {0}.gz".format(fname))
                with gzip.open(fname + '.gz', 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            logging.warning("Removing {}".format(fname))
            os.remove(fname)
        except Exception as e:
            logging.error(e)

    def writerow(self, row):
        """

        :param row:
        :return:
        """
        out_txt = json.dumps(row) + "\n"
        self._bytes_written += self._out_fh.write(out_txt)
        self._out_fh.flush()
        if self._bytes_written > self.max_bytes:
            self.close()
            self._compress(self.fname)
            self._make_writer()

        return out_txt
