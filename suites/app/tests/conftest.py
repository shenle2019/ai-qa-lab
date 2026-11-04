import pytest

from libs.miniappium import Device


@pytest.fixture(scope="session")
def device():
    try:
        instance = Device.connect()
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"no Android device: {exc}")
    return instance
