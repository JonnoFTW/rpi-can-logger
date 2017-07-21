import csv
from datetime import datetime
import subprocess
from pathlib import Path
import logging
from io import StringIO

class CSVLogRotator:
    """

    """

    def __init__(self, log_folder, maxbytes, fieldnames):
        """

        :param log_folder:
        :param maxbytes:
        :param fieldnames:
        """
        if maxbytes < 512 or type(maxbytes) is not int:
            raise ValueError("Please specify a integer maxbytes >= 512")
        self.log_folder = log_folder
        self.max_bytes = maxbytes
        self.fieldnames = fieldnames
        self._make_csv_writer()

    def _make_csv_writer(self):
        """

        :return:
        """
        self._reset_buffer()
        self._bytes_written = 0
        now = datetime.now()
        self._out_csv = open(self.log_folder + '/' + now.strftime('%Y%m%d_%H%M%S.csv'), 'w')
        logging.warning("Writing to {} ({} bytes)".format(self._out_csv.name, self.max_bytes))
        self._out_writer = csv.DictWriter(self._buffer, fieldnames=self.fieldnames, restval=None)
        self._out_writer.writeheader()
        self._out_csv.write(self._buffer.getvalue())
        self._reset_buffer()

    def _reset_buffer(self):
        self._buffer = StringIO()

    def close(self):
        """

        :return:
        """
        self._out_csv.close()

    def writerow(self, row):
        """

        :param row:
        :return:
        """
        self._bytes_written += self._out_writer.writerow(row)
        row_txt = self._buffer.getvalue()
        self._out_csv.write(row_txt)
        self._reset_buffer()
        self._out_csv.flush()
        if self._bytes_written > self.max_bytes:
            self._out_csv.close()
            self._make_csv_writer()
            out_name = str(Path(self._out_csv.name).absolute())
            subprocess.Popen(['7z', 'a', '-t7z', '-m0=lzma', '-mx=9', '-mfb=64', '-md=16m',
                              out_name + '.7z', out_name])

        return row_txt
