from libs.miniappium import Device
from libs.minipytest import fixture, skip

collect_ignore_glob = ["**/test_*.py"]


@fixture(scope="session")
def device():
    try:
        instance = Device.connect()
    except Exception as exc:
        skip(f"no Android device: {exc}")
    yield instance
