import pytest
from unittest.mock import MagicMock
from metriq_gym.run import setup_device, QBraidSetupError


@pytest.fixture
def mock_provider():
    return MagicMock()


@pytest.fixture
def mock_device():
    return MagicMock()


@pytest.fixture
def patch_load_provider(mock_provider, monkeypatch):
    monkeypatch.setattr("metriq_gym.run.load_provider", lambda _: mock_provider)


def test_setup_device_success(mock_provider, mock_device, patch_load_provider):
    mock_provider.get_device.return_value = mock_device

    provider_name = "test_provider"
    backend_name = "test_backend"

    device = setup_device(provider_name, backend_name)

    mock_provider.get_device.assert_called_once_with(backend_name)
    assert device == mock_device


def test_setup_device_failure(mock_provider, patch_load_provider, caplog):
    mock_provider.get_device.side_effect = Exception()
    mock_provider.get_devices.return_value = [MagicMock(id="device1"), MagicMock(id="device2")]

    provider_name = "test_provider"
    backend_name = "non_existent_backend"

    with pytest.raises(QBraidSetupError, match="Device not found"):
        setup_device(provider_name, backend_name)

    # Verify the printed output
    assert (
        f"No device matching the name '{backend_name}' found in provider '{provider_name}'."
        in caplog.text
    )
    assert "Devices available: ['device1', 'device2']" in caplog.text
