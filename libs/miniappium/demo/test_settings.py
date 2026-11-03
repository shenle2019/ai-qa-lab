from pathlib import Path

from libs.miniappium import expect
from libs.minipytest import mark

ROOT = Path(__file__).resolve().parents[3]
SHOTS = ROOT / "docs" / "portfolio" / "screenshots"


@mark.smoke
def test_settings_home(device):
    device.start_settings()
    home = device.wait_for(text="Search Settings", timeout=10)
    expect(home).to_be_visible()
    device.screenshot(SHOTS / "module-05-settings.png")


def test_open_network(device):
    device.start_settings()
    device.wait_for(text="Network & internet", timeout=10).tap()
    internet = device.wait_for(text="Internet", timeout=10)
    expect(internet).to_be_visible()
    device.screenshot(SHOTS / "module-05-network.png")


def test_back_returns_home(device):
    device.start_settings()
    device.wait_for(text="Network & internet", timeout=10).tap()
    device.wait_for(text="Internet", timeout=10)
    device.press_back()
    home = device.wait_for(text="Search Settings", timeout=10)
    expect(home).to_be_visible()
