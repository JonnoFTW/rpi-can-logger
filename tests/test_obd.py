from rpi_can_logger.logger import obd_pids

#check there are no dups

def test_dups():
    ids = [p.pid for p in obd_pids]
    assert len(set(ids)) == len(ids)

