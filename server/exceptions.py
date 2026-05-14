"""Custom exceptions for the MATLAB Engine interface."""


class MatlabCallError(RuntimeError):
    """Raised when a MATLAB function call fails."""

    def __init__(self, func_name: str, args_passed: tuple, message: str):
        self.func_name = func_name
        self.args_passed = args_passed
        self.original_message = message
        super().__init__(
            f"MATLAB call failed: {func_name}({', '.join(repr(a) for a in args_passed)}) — {message}"
        )


class SimulinkError(RuntimeError):
    """Raised when a Simulink simulation step fails (divergence, timeout, etc.)."""
    pass
