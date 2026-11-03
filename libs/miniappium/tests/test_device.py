from libs.miniappium import expect


def test_device_connected(device):
    assert device.serial
    assert device.model()


def test_settings_home(device):
    device.start_settings()
    element = device.wait_for(text="Search Settings", timeout=10)
    expect(element).to_be_visible()


def test_tap_network_and_open(device):
    device.start_settings()
    element = device.wait_for(text="Network & internet", timeout=10)
    element.tap()
    internet = device.wait_for(text="Internet", timeout=10)
    expect(internet).to_be_visible()


def test_back_returns_home(device):
    device.start_settings()
    device.wait_for(text="Network & internet", timeout=10).tap()
    device.wait_for(text="Internet", timeout=10)
    device.press_back()
    home = device.wait_for(text="Search Settings", timeout=10)
    expect(home).to_be_visible()


def test_screenshot(device, tmp_path):
    device.start_settings()
    device.wait_for(text="Search Settings", timeout=10)
    target = device.screenshot(tmp_path / "settings.png")
    assert target.exists()
    assert target.stat().st_size > 1000
