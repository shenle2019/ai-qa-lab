import time

from libs.miniappium import expect

SEARCH = "com.google.android.settings.intelligence:id/open_search_view_edit_text"


def _home(device):
    device.start_settings()
    last = None
    for _ in range(2):
        try:
            return device.wait_for(text="Search Settings", timeout=20)
        except Exception as exc:
            last = exc
            device.press_back()
            time.sleep(0.5)
    raise last


def _wait_back(device, timeout: float = 10.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if device.find(content_desc="Navigate up") or device.find(content_desc="Back"):
            return
        time.sleep(0.3)
    raise AssertionError("back button not found")


def test_model(device):
    assert device.model()


def test_serial(device):
    assert device.serial


def test_home_search_visible(device):
    expect(_home(device)).to_be_visible()


def test_home_network_visible(device):
    _home(device)
    expect(device.wait_for(text="Network & internet")).to_be_visible()


def test_home_connected_devices_visible(device):
    _home(device)
    expect(device.wait_for(text="Connected devices")).to_be_visible()


def test_home_apps_visible(device):
    _home(device)
    expect(device.wait_for(text="Apps")).to_be_visible()


def test_home_notifications_visible(device):
    _home(device)
    expect(device.wait_for(text="Notifications")).to_be_visible()


def test_home_sound_visible(device):
    _home(device)
    expect(device.wait_for(text="Sound & vibration")).to_be_visible()


def test_home_modes_visible(device):
    _home(device)
    expect(device.wait_for(text="Modes")).to_be_visible()


def test_home_display_visible(device):
    _home(device)
    expect(device.wait_for(text="Display & touch")).to_be_visible()


def test_home_google_visible(device):
    _home(device)
    expect(device.wait_for(text="Google")).to_be_visible()


def test_open_network(device):
    _home(device)
    device.wait_for(text="Network & internet").tap()
    expect(device.wait_for(text="Internet", timeout=10)).to_be_visible()


def test_open_apps(device):
    _home(device)
    device.wait_for(text="Apps").tap()
    _wait_back(device)


def test_open_notifications(device):
    _home(device)
    device.wait_for(text="Notifications").tap()
    _wait_back(device)


def test_open_sound(device):
    _home(device)
    device.wait_for(text="Sound & vibration").tap()
    _wait_back(device)


def test_open_display(device):
    _home(device)
    device.wait_for(text="Display & touch").tap()
    _wait_back(device)


def test_open_connected_devices(device):
    _home(device)
    device.wait_for(text="Connected devices").tap()
    _wait_back(device)


def test_home_search_bar_visible(device):
    _home(device)
    expect(device.wait_for(resource_id="com.android.settings:id/search_action_bar")).to_be_visible()


def test_back_from_network(device):
    _home(device)
    device.wait_for(text="Network & internet").tap()
    device.wait_for(text="Internet", timeout=10)
    for _ in range(3):
        device.press_back()
        try:
            home = device.wait_for(text="Search Settings", timeout=5)
            expect(home).to_be_visible()
            return
        except Exception:
            continue
    raise AssertionError("did not return home")


def test_search_wifi(device):
    _home(device)
    device.wait_for(text="Search Settings").tap()
    device.wait_for(resource_id=SEARCH, timeout=10).tap()
    device.input_text("wifi")
    expect(device.wait_for(text="Wi-Fi", timeout=10)).to_be_visible()


def test_swipe_home(device):
    _home(device)
    device.swipe(540, 1800, 540, 600, 400)
    _home(device)


def test_screenshot(device, tmp_path):
    _home(device)
    target = device.screenshot(tmp_path / "settings-suite.png")
    assert target.exists()
    assert target.stat().st_size > 1000


def test_current_activity(device):
    _home(device)
    activity = device.current_activity()
    assert "settings" in activity.lower()


def test_home_key_and_restart(device):
    _home(device)
    device.press_home()
    time.sleep(0.5)
    device.start_settings()
    expect(device.wait_for(text="Search Settings", timeout=10)).to_be_visible()
