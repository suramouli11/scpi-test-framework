import pytest
from instrument_sim.mock_signal_generator import start_server
from driver.signal_generator import SignalGeneratorDriver
import logging



@pytest.fixture(scope="session")
def instrument_server():
    """Starts the mock instrument once for the whole test run — not once per test."""
    server, port = start_server()
    yield port
    server.shutdown()


@pytest.fixture
def driver(instrument_server):
    """Gives each test a fresh, reset driver connection. Runs before AND after the test."""
    gen = SignalGeneratorDriver(port=instrument_server)
    gen.reset()
    yield gen
    gen.close()


logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@pytest.fixture(autouse=True)
def capture_state_on_failure(request, instrument_server):
    """
    Runs around EVERY test automatically (autouse=True).
    If the test fails, connects fresh and logs a full instrument
    state snapshot -- this is your root-cause starting point instead
    of re-running the test by hand to guess what state it was in.
    """
    yield
    if request.node.rep_call.failed:
        from driver.signal_generator import SignalGeneratorDriver
        diag = SignalGeneratorDriver(port=instrument_server)
        state = diag.snapshot()
        logging.getLogger("failure_diagnostics").error(
            "TEST FAILED: %s -- instrument state at failure: %s",
            request.node.name, state
        )
        diag.close()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Pytest hook: stores the pass/fail result on the test item itself
    (as `rep_call`) so other fixtures -- like the one above -- can check
    "did the test I'm attached to actually fail?"
    """
    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)