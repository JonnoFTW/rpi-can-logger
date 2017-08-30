import abc


class BaseLogRotator:
    def __init__(self, log_folder, maxbytes, fieldnames, vin):
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
        self.vin = vin
        self._make_writer()

    @abc.abstractmethod
    def _make_writer(self):
        """
        inititialises the writer
        :return:
        """
        return
