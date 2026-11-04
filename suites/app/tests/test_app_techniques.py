"""App cases: offline UIAutomator element parsing plus on-device scenarios.

On-device cases skip automatically when no Android device is connected.
"""

import time

import pytest

from libs.miniappium import Element, MiniAppiumError, expect


class FakeDevice:
    def __init__(self):
        self.taps = []

    def tap(self, x, y):
        self.taps.append((x, y))
        return self


def _element(**attributes):
    base = {
        "text": "Network & internet",
        "resource-id": "android:id/title",
        "content-desc": "network",
        "class": "android.widget.TextView",
        "bounds": "[10,20][110,220]",
    }
    base.update(attributes)
    return Element(FakeDevice(), base)


def test_element_text():
    assert _element().text == "Network & internet"


def test_element_resource_id():
    assert _element().resource_id == "android:id/title"


def test_element_content_desc():
    assert _element().content_desc == "network"


def test_element_class_name():
    assert _element().class_name == "android.widget.TextView"


def test_element_bounds_parse():
    assert _element().bounds == (10, 20, 110, 220)


def test_element_center():
    assert _element().center() == (60, 120)


def test_element_visible_with_area():
    assert _element().is_visible() is True


def test_element_invisible_zero_width():
    assert _element(bounds="[10,20][10,220]").is_visible() is False


def test_element_invisible_without_bounds():
    assert _element(bounds="").bounds is None
    assert _element(bounds="").center() is None
    assert _element(bounds="").is_visible() is False


def test_element_tap_uses_center():
    element = _element()
    element.tap()
    assert element.device.taps == [(60, 120)]


def test_element_tap_without_bounds_raises():
    with pytest.raises(MiniAppiumError):
        _element(bounds="").tap()


def test_element_repr_contains_text():
    assert "Network & internet" in repr(_element())


def _home(device):
    device.start_settings()
    last = None
    for _ in range(2):
        try:
            return device.wait_for(text="Search Settings", timeout=20)
        except Exception as exc:  # noqa: BLE001
            last = exc
            device.press_back()
            time.sleep(0.5)
    raise last


def test_device_model(device):
    assert device.model()


def test_device_serial(device):
    assert device.serial


def test_settings_home_visible(device):
    expect(_home(device)).to_be_visible()


@pytest.mark.parametrize(
    "label",
    ["Network & internet", "Connected devices", "Apps", "Notifications", "Display & touch"],
)
def test_settings_entries_visible(device, label):
    _home(device)
    expect(device.wait_for(text=label, timeout=10)).to_be_visible()


def test_open_network(device):
    _home(device)
    device.wait_for(text="Network & internet", timeout=10).tap()
    expect(device.wait_for(text="Internet", timeout=10)).to_be_visible()


def test_open_apps_and_back(device):
    _home(device)
    device.wait_for(text="Apps", timeout=10).tap()
    device.press_back()
    expect(device.wait_for(text="Search Settings", timeout=10)).to_be_visible()


def test_press_home_stays_in_launcher(device):
    device.start_settings()
    device.press_home()
    time.sleep(1)
    assert device.current_activity()


def test_screenshot_saved(device, tmp_path):
    _home(device)
    target = device.screenshot(tmp_path / "settings.png")
    assert target.exists()
    assert target.stat().st_size > 1000


def test_current_activity_is_settings(device):
    _home(device)
    assert "settings" in device.current_activity().lower()
