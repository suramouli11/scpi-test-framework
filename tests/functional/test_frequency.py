import pytest


@pytest.mark.functional
def test_set_and_get_frequency(driver):
    driver.set_frequency(1_000_000_000)
    assert driver.get_frequency() == 1_000_000_000


@pytest.mark.functional
def test_identity_string_contains_manufacturer(driver):
    idn = driver.get_idn()
    assert "R&S" in idn

