from os import _exit, fork, getpid, wait

import pytest

import univention.updater.locking as L


@pytest.fixture(autouse=True)
def lock(tmpdir, monkeypatch):
    lock = tmpdir / "lock"
    monkeypatch.setattr(L, "UPDATER_LOCK_FILE_NAME", str(lock))
    return lock


def test_empty(lock):
    lock.write("")
    with L.UpdaterLock():
        assert lock.exists()
        assert lock.read() == '%d\n' % getpid()


def test_stale(lock, capsys):
    lock.write("%d\n" % 0x7ffffff)
    with L.UpdaterLock():
        assert lock.exists()
        assert lock.read() == '%d\n' % getpid()

    out, err = capsys.readouterr()
    assert out == ""
    # assert "Stale PID " in err


def test_context(lock):
    with L.UpdaterLock():
        assert lock.exists()
        assert lock.read() == '%d\n' % getpid()


def test_recursive(lock):
    with L.UpdaterLock(1) as l1:
        assert l1.lock == 0
        with L.UpdaterLock(1) as l2:
            assert l2.lock == 0
            assert lock.exists()
            assert lock.read() == '%d\n' % getpid()

        assert not lock.exists()


@pytest.mark.timeout(timeout=5)
def test_parent(lock):
    ppid = '%d\n' % getpid()

    with L.UpdaterLock(1) as l1:
        pid = fork()
        if not pid:
            with L.UpdaterLock(1) as l2:
                assert l2.lock == 1
                assert lock.exists()
                assert lock.read() == ppid
                _exit(0)

        (cpid, status) = wait()
        assert pid == cpid
        assert status == 0

        assert lock.exists()
        assert lock.read() == ppid


@pytest.mark.parametrize('data', ["INVALID", "\u20ac"])
def test_invalid(data, lock):
    lock.write(data)

    with pytest.raises(L.LockingError) as exc_info:
        l = L.UpdaterLock(1)
        l.updater_lock_acquire()
        assert False

    assert "Invalid PID" in str(exc_info.value)


@pytest.mark.timeout(timeout=5)
def test_timeout(mocker, lock):
    mocker.patch("os.getppid").return_value = -1
    lock.write("1\n")

    with pytest.raises(L.LockingError) as exc_info:
        l = L.UpdaterLock(1)
        l.updater_lock_acquire()
        assert False

    assert "Another updater process 1 is currently running according to " in str(exc_info.value)
