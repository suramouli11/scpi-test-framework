import socket
import time
import pytest


@pytest.mark.regression
def test_server_process_does_not_hang_on_client_disconnect(instrument_server):
    """
    Regression test for: per-connection handler threads defaulted to
    non-daemon, which kept the server process alive forever even after
    clients disconnected and the test session tried to exit.

    We can't directly test "does the whole process exit" from inside
    pytest, but we CAN verify the underlying setting that caused the bug
    is still correctly configured.
    """
    from instrument_sim.mock_signal_generator import MockInstrumentServer
    assert MockInstrumentServer.daemon_threads is True


@pytest.mark.regression
def test_back_to_back_commands_are_not_merged(instrument_server):
    """
    Regression test for: sending two commands back-to-back without
    waiting for a reply could arrive at the server as a single recv()
    chunk (e.g. "OUTP:STAT ON\\nOUTP:STAT?"), which the old dispatch()
    treated as one unrecognized command -- silently swallowing the query
    and hanging the client forever waiting for a reply that never came.
    """
    s = socket.socket()
    s.settimeout(3)
    s.connect(("127.0.0.1", instrument_server))

    # Fire two commands rapidly, back-to-back, like the original bug scenario
    s.sendall(b"OUTP:STAT ON\n")
    s.sendall(b"OUTP:STAT?\n")

    # This must NOT time out. If framing breaks again, this line hangs/fails.
    response = s.recv(1024).decode().strip()
    assert response == "1"

    s.close()