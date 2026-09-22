import socket
import logging

logger = logging.getLogger("signal_generator")


class SignalGeneratorDriver:
    """
    Clean Python interface to the signal generator, hiding SCPI/socket details.
    Tests should only ever talk to this class, never raw sockets.
    """

    def __init__(self, host="127.0.0.1", port=5025, timeout=3):
        self._sock = socket.socket()
        self._sock.settimeout(timeout)
        self._sock.connect((host, port))
        logger.info("Connected to instrument at %s:%s", host, port)

    def _send(self, cmd: str):
        logger.debug("SEND: %s", cmd)
        self._sock.sendall((cmd + "\n").encode())

    def _query(self, cmd: str) -> str:
        self._send(cmd)
        response = self._sock.recv(1024).decode().strip()
        logger.debug("RECV: %s", response)
        return response

    def get_idn(self) -> str:
        return self._query("*IDN?")

    def reset(self):
        self._send("*RST")

    def set_frequency(self, hz: float):
        self._send(f"SOUR:FREQ {hz}")

    def get_frequency(self) -> float:
        return float(self._query("SOUR:FREQ?"))

    def set_power(self, dbm: float):
        self._send(f"SOUR:POW {dbm}")

    def get_power(self) -> float:
        return float(self._query("SOUR:POW?"))

    def set_output(self, on: bool):
        self._send(f"OUTP:STAT {'ON' if on else 'OFF'}")

    def get_output(self) -> bool:
        return self._query("OUTP:STAT?") == "1"

    def get_last_error(self) -> str:
        return self._query("SYST:ERR?")

    def snapshot(self) -> dict:
        """Captures full instrument state — used for failure diagnostics."""
        return {
            "frequency_hz": self.get_frequency(),
            "power_dbm": self.get_power(),
            "output_on": self.get_output(),
        }

    def close(self):
        self._sock.close()
        logger.info("Connection closed")