import pytest


@pytest.mark.system
def test_full_instrument_lifecycle(driver):
    # 1. Start from a known clean state
    driver.reset()
    assert driver.get_output() is False

    # 2. Configure the instrument like a real user would
    driver.set_frequency(5_800_000_000)   # 5.8 GHz
    driver.set_power(0)
    driver.set_output(True)

    assert driver.get_frequency() == 5_800_000_000
    assert driver.get_power() == 0
    assert driver.get_output() is True

    # 3. Attempt an invalid operation mid-session
    driver.set_frequency(999_000_000_000)  # way above MAX_FREQ
    error = driver.get_last_error()
    assert "Data out of range" in error

    # 4. Confirm the invalid command did NOT corrupt existing state
    assert driver.get_frequency() == 5_800_000_000

    # 5. Safely power down
    driver.set_output(False)
    assert driver.get_output() is False

    # 6. Error queue should be clean now (we already drained the one error)
    assert driver.get_last_error() == '0,"No error"'