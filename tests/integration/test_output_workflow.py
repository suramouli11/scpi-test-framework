import pytest


@pytest.mark.integration
def test_configure_and_enable_output(driver):
    driver.set_frequency(2_400_000_000)  # 2.4 GHz
    driver.set_power(-5)
    driver.set_output(True)

    assert driver.get_frequency() == 2_400_000_000
    assert driver.get_power() == -5
    assert driver.get_output() is True


@pytest.mark.integration
def test_output_defaults_to_off_after_reset(driver):
    driver.set_output(True)
    driver.reset()
    assert driver.get_output() is False