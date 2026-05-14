"""MATLAB Engine session manager — singleton, lazy-start, passive reconnect.

All tools share one MATLAB session. The session starts on the first tool call
(~20 s cold start). Subsequent calls reuse the running engine.

Environment variables
---------------------
SLX_HELPERS_PATH : override the default ``../matlab`` directory for MATLAB helpers.
"""

from __future__ import annotations

import io
import logging
import os
import time
from pathlib import Path
from typing import Any, Optional

from .exceptions import MatlabCallError

logger = logging.getLogger(__name__)

_matlab_engine = None


def _get_matlab_engine():
    global _matlab_engine
    if _matlab_engine is None:
        try:
            import matlab.engine as _me
            _matlab_engine = _me
        except ImportError:
            pass
    return _matlab_engine


def _log_matlab_output(label: str, stdout: Any, stderr: Any) -> None:
    stdout_text = stdout.getvalue() if hasattr(stdout, "getvalue") else ""
    stderr_text = stderr.getvalue() if hasattr(stderr, "getvalue") else ""
    if stdout_text.strip():
        logger.debug("MATLAB stdout [%s]: %s", label, stdout_text.strip())
    if stderr_text.strip():
        logger.warning("MATLAB stderr [%s]: %s", label, stderr_text.strip())


class MatlabSession:
    """Singleton MATLAB Engine session.

    Usage::

        session = MatlabSession.get()
        result = session.call('sqrt', 4.0)
        session.close()
    """

    _instances: dict[str, "MatlabSession"] = {}

    def __init__(self) -> None:
        self._eng: Any = None
        self._session_id: Optional[str] = None
        # Resolve MATLAB helper path: env var > default ../matlab relative to this file
        env_path = os.environ.get("SLX_HELPERS_PATH", "")
        if env_path and Path(env_path).is_dir():
            self._helper_paths: list[str] = [str(Path(env_path).resolve())]
        else:
            default_helpers = Path(__file__).resolve().parent.parent / "matlab"
            self._helper_paths = [str(default_helpers)] if default_helpers.is_dir() else []

    @classmethod
    def get(cls, session_id: str = "default") -> "MatlabSession":
        if session_id not in cls._instances:
            inst = cls()
            inst._session_id = session_id
            cls._instances[session_id] = inst
        return cls._instances[session_id]

    def _connect(self) -> None:
        if self._eng is not None:
            return
        me = _get_matlab_engine()
        if me is None:
            raise RuntimeError(
                "matlab.engine not available. Install via: pip install matlabengine"
            )
        logger.info("Starting MATLAB engine (session=%s) …", self._session_id)
        self._eng = me.start_matlab()
        for helper_path in self._helper_paths:
            if os.path.isdir(helper_path):
                self._eng.addpath(helper_path, nargout=0)
                logger.debug("Added to MATLAB path: %s", helper_path)
            else:
                logger.warning("MATLAB helper dir not found: %s", helper_path)
        try:
            self._eng.feature("DefaultCharacterSet", "UTF-8", nargout=0)
        except Exception as exc:
            logger.warning("Could not set MATLAB DefaultCharacterSet=UTF-8: %s", exc)
        logger.info("MATLAB engine ready (session=%s).", self._session_id)

    def _get_engine(self) -> Any:
        if self._eng is None:
            self._connect()
        return self._eng

    @staticmethod
    def _is_communication_error(exc: Exception) -> bool:
        msg = str(exc).lower()
        return any(kw in msg for kw in ("rpc", "connection", "pipe", "broken", "terminated"))

    @staticmethod
    def _format_exception_message(exc: Exception) -> str:
        generic_messages = {"unknown exception", "exception", exc.__class__.__name__.lower()}
        ordered: list[str] = []

        def add(candidate: Any) -> None:
            if candidate in (None, ""):
                return
            text = str(candidate).strip()
            if text and text not in ordered:
                ordered.append(text)

        add(getattr(exc, "message", None))
        for arg in getattr(exc, "args", ()):
            add(arg)
        add(str(exc))
        add(getattr(exc, "reason", None))
        if exc.__cause__ is not None:
            add(exc.__cause__)

        specific = [t for t in ordered if t.lower() not in generic_messages]
        return "; ".join(specific) if specific else (ordered[0] if ordered else exc.__class__.__name__)

    def call(self, func_name: str, *args: Any, nargout: int = 1, **kwargs: Any) -> Any:
        """Call a MATLAB function by name with passive reconnect."""
        eng = self._get_engine()
        t0 = time.perf_counter()
        timeout = kwargs.pop("timeout", None)
        _stdout: Any = kwargs.pop("stdout", io.StringIO())
        _stderr: Any = kwargs.pop("stderr", io.StringIO())

        def _invoke(target_eng: Any) -> Any:
            if timeout is None:
                return getattr(target_eng, func_name)(
                    *args, nargout=nargout, stdout=_stdout, stderr=_stderr, **kwargs
                )
            call_kwargs = dict(kwargs)
            call_kwargs["background"] = True
            future = getattr(target_eng, func_name)(*args, nargout=nargout, **call_kwargs)
            if not hasattr(future, "result"):
                return future
            try:
                return future.result(timeout=timeout)
            except Exception as exc:
                if "timeout" in exc.__class__.__name__.lower():
                    raise TimeoutError(f"Timed out after {timeout}s") from exc
                raise

        try:
            result = _invoke(eng)
        except Exception as exc:
            if self._is_communication_error(exc):
                logger.warning("MATLAB engine lost, reconnecting …")
                self._eng = None
                eng = self._get_engine()
                try:
                    result = _invoke(eng)
                except Exception as exc2:
                    raise MatlabCallError(func_name, args, self._format_exception_message(exc2)) from exc2
            else:
                raise MatlabCallError(func_name, args, self._format_exception_message(exc)) from exc

        elapsed = (time.perf_counter() - t0) * 1000
        logger.debug("MATLAB %s() -> %.1f ms", func_name, elapsed)
        _log_matlab_output(func_name, _stdout, _stderr)
        return result

    def eval(self, code: str, nargout: int = 0) -> Any:
        """Execute raw MATLAB code string."""
        eng = self._get_engine()
        _stdout = io.StringIO()
        _stderr = io.StringIO()
        try:
            result = eng.eval(code, nargout=nargout, stdout=_stdout, stderr=_stderr)
            _log_matlab_output(f"eval({code!r})", _stdout, _stderr)
            return result
        except Exception as exc:
            if self._is_communication_error(exc):
                _log_matlab_output(f"eval({code!r})", _stdout, _stderr)
                logger.warning("MATLAB engine lost, reconnecting …")
                self._eng = None
                eng = self._get_engine()
                _stdout2, _stderr2 = io.StringIO(), io.StringIO()
                try:
                    result = eng.eval(code, nargout=nargout, stdout=_stdout2, stderr=_stderr2)
                    _log_matlab_output(f"eval({code!r})", _stdout2, _stderr2)
                    return result
                except Exception as exc2:
                    raise MatlabCallError(f"eval({code!r})", (), self._format_exception_message(exc2)) from exc2
            else:
                raise MatlabCallError(f"eval({code!r})", (), self._format_exception_message(exc)) from exc

    @property
    def engine(self) -> Any:
        return self._get_engine()

    def close(self) -> None:
        if self._eng is not None:
            try:
                self._eng.quit()
            except Exception:
                pass
            self._eng = None
        if self._session_id and self._session_id in self._instances:
            del self._instances[self._session_id]
        logger.info("MATLAB session '%s' closed.", self._session_id)
