"""
Mock Signal Generator - simulates a SCPI-controlled RF signal generator over TCP.

This stands in for real lab hardware so the test framework can run
functional/integration/regression/system tests without a physical instrument.
"""
from collections import deque
import socketserver
import threading


class InstrumentState:
    """Holds the simulated instrument's internal state."""

    def __init__(self):
        self.frequency_hz = 1_000_000_000.0  # default 1 GHz
        self.power_dbm = -10.0
        self.output_on = False
        self.MIN_FREQ = 9_000.0          # 9 kHz
        self.MAX_FREQ = 6_000_000_000.0  # 6 GHz
        self.MIN_POWER = -30.0
        self.MAX_POWER = 20.0
        self.error_queue = deque()  # real SCPI instruments queue errors, not inline replies

    def reset(self):
        self.__init__()

    def push_error(self, code, message):
        self.error_queue.append(f'{code},"{message}"')

    def pop_error(self):
        if self.error_queue:
            return self.error_queue.popleft()
        return '0,"No error"'


class SCPIHandler(socketserver.BaseRequestHandler):
    """Parses SCPI-like commands and updates/reads shared instrument state."""

    def handle(self):
        buffer = ""
        while True:
            try:
                chunk = self.request.recv(1024).decode("utf-8")
            except ConnectionResetError:
                break
            if not chunk:
                break

            buffer += chunk
            # A single recv() can contain zero, one, or several full commands,
            # or a partial command that finishes on the next recv() — so we
            # only ever act on complete, newline-terminated lines.
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if not line:
                    continue
                response = self.dispatch(line)
                if response is not None:
                    self.request.sendall((response + "\n").encode("utf-8"))

    def dispatch(self, command: str):
        state: InstrumentState = self.server.state
        cmd = command.upper()

        try:
            if cmd == "*IDN?":
                return "R&S,MOCK-SGEN,SN123456,FW1.0"

            if cmd == "*RST":
                state.reset()
                return None  # commands (non-queries) return no response, like real SCPI

            if cmd == "SYST:ERR?":
                return state.pop_error()

            if cmd.startswith("SOUR:FREQ?") or cmd == "SOUR:FREQ?":
                return str(state.frequency_hz)

            if cmd.startswith("SOUR:FREQ "):
                value = float(command.split(" ", 1)[1])
                if not (state.MIN_FREQ <= value <= state.MAX_FREQ):
                    state.push_error(-222, "Data out of range")
                    return None
                state.frequency_hz = value
                return None

            if cmd == "SOUR:POW?":
                return str(state.power_dbm)

            if cmd.startswith("SOUR:POW "):
                value = float(command.split(" ", 1)[1])
                if not (state.MIN_POWER <= value <= state.MAX_POWER):
                    state.push_error(-222, "Data out of range")
                    return None
                state.power_dbm = value
                return None

            if cmd == "OUTP:STAT?":
                return "1" if state.output_on else "0"

            if cmd.startswith("OUTP:STAT "):
                value = command.split(" ", 1)[1].strip().upper()
                if value in ("ON", "1"):
                    state.output_on = True
                elif value in ("OFF", "0"):
                    state.output_on = False
                else:
                    state.push_error(-224, "Illegal parameter value")
                return None

            state.push_error(-113, "Undefined header")
            return None

        except (ValueError, IndexError):
            state.push_error(-108, "Parameter error")
            return None


class MockInstrumentServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True  # don't let per-connection threads block process exit

    def __init__(self, host="127.0.0.1", port=0):
        super().__init__((host, port), SCPIHandler)
        self.state = InstrumentState()


def start_server(host="127.0.0.1", port=0):
    """Starts the mock instrument in a background thread. Returns (server, port)."""
    server = MockInstrumentServer(host, port)
    actual_port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, actual_port


if __name__ == "__main__":
    srv, port = start_server(port=5025)
    print(f"Mock signal generator listening on 127.0.0.1:{port}")
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        srv.shutdown()