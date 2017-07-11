from rpi_can_logger.logger import _pids

#check there are no dups

def test_dups():
    ids = [p.pid for p in _pids]
    assert len(set(ids)) == len(ids)

