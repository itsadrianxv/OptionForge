from __future__ import annotations

import threading
from dataclasses import dataclass
from types import SimpleNamespace

import pytest

import src.main.config.gateway_manager as gateway_manager_module
from src.main.config.gateway_manager import GatewayManager, GatewayStatus


class FakeEventEngine:
    def __init__(self) -> None:
        self.handlers = {}

    def register(self, event_type, handler) -> None:
        self.handlers.setdefault(event_type, []).append(handler)

    def unregister(self, event_type, handler) -> None:
        handlers = self.handlers.get(event_type, [])
        if handler in handlers:
            handlers.remove(handler)

    def emit(self, event_type, data=None) -> None:
        event = SimpleNamespace(type=event_type, data=data)
        for handler in list(self.handlers.get(event_type, [])):
            handler(event)


@dataclass
class FakeTdApi:
    connect_status: bool = False
    login_status: bool = False
    auth_status: bool = False
    contract_inited: bool = False


@dataclass
class FakeMdApi:
    connect_status: bool = False
    login_status: bool = False


class FakeGateway:
    def __init__(self, td_api: FakeTdApi, md_api: FakeMdApi) -> None:
        self.td_api = td_api
        self.md_api = md_api


class FakeMainEngine:
    def __init__(self, gateway: FakeGateway) -> None:
        self.event_engine = FakeEventEngine()
        self.gateway = gateway
        self.connect_calls = []
        self.contracts = []

    def add_gateway(self, gateway_class) -> None:
        return None

    def connect(self, setting, gateway_name) -> None:
        self.connect_calls.append((setting, gateway_name))

    def close(self) -> None:
        return None

    def get_gateway(self, gateway_name):
        if gateway_name in {"ctp", "CTP"}:
            return self.gateway
        return None

    def get_all_contracts(self):
        return self.contracts


class FakeTimer:
    created = []

    def __init__(self, delay, callback, args=None, kwargs=None) -> None:
        self.delay = delay
        self.callback = callback
        self.args = args or ()
        self.kwargs = kwargs or {}
        self.daemon = False
        self.started = False
        self.cancelled = False
        self.__class__.created.append(self)

    def start(self) -> None:
        self.started = True

    def cancel(self) -> None:
        self.cancelled = True

    def fire(self) -> None:
        self.callback(*self.args, **self.kwargs)


def _build_manager(
    *,
    td_connected: bool,
    td_login: bool,
    md_connected: bool,
    md_login: bool,
    contract_inited: bool,
    auth_status: bool = False,
    auth_code: str = "",
):
    td_api = FakeTdApi(
        connect_status=td_connected,
        login_status=td_login,
        auth_status=auth_status,
        contract_inited=contract_inited,
    )
    md_api = FakeMdApi(connect_status=md_connected, login_status=md_login)
    gateway = FakeGateway(td_api=td_api, md_api=md_api)
    main_engine = FakeMainEngine(gateway)
    if contract_inited:
        main_engine.contracts = [SimpleNamespace(gateway_name="CTP")]

    manager = GatewayManager(main_engine)
    manager.set_config({"ctp": {"授权编码": auth_code}})
    return manager, main_engine, gateway


def test_wait_for_ready_accepts_trading_profile_without_auth_requirement() -> None:
    manager, main_engine, _ = _build_manager(
        td_connected=True,
        td_login=True,
        md_connected=True,
        md_login=True,
        contract_inited=True,
        auth_status=False,
        auth_code="",
    )

    states = manager.wait_for_ready("trading", timeout=0.1, check_interval=0.01)

    assert states["ctp"].status == GatewayStatus.CONNECTED
    assert {
        gateway_manager_module.EVENT_LOG,
        gateway_manager_module.EVENT_CONTRACT,
        gateway_manager_module.EVENT_ACCOUNT,
        gateway_manager_module.EVENT_POSITION,
    }.issubset(set(main_engine.event_engine.handlers))


def test_wait_for_ready_requires_auth_status_when_auth_code_present() -> None:
    manager, _, _ = _build_manager(
        td_connected=True,
        td_login=True,
        md_connected=True,
        md_login=True,
        contract_inited=True,
        auth_status=False,
        auth_code="auth-code",
    )

    with pytest.raises(TimeoutError, match=r"td=auth"):
        manager.wait_for_ready("trading", timeout=0.05, check_interval=0.01)


def test_wait_for_ready_times_out_when_contracts_are_still_loading() -> None:
    manager, _, gateway = _build_manager(
        td_connected=True,
        td_login=True,
        md_connected=True,
        md_login=False,
        contract_inited=False,
    )

    def mark_ready() -> None:
        gateway.md_api.login_status = True

    timer = threading.Timer(0.01, mark_ready)
    timer.start()

    with pytest.raises(TimeoutError, match=r"contracts=loading"):
        manager.wait_for_ready("trading", timeout=0.03, check_interval=0.005)


def test_gateway_manager_degrades_and_limits_reconnect_attempts(monkeypatch) -> None:
    FakeTimer.created = []
    monkeypatch.setattr(gateway_manager_module.threading, "Timer", FakeTimer)

    manager, main_engine, gateway = _build_manager(
        td_connected=True,
        td_login=True,
        md_connected=True,
        md_login=True,
        contract_inited=True,
    )
    manager.wait_for_ready("trading", timeout=0.1, check_interval=0.01)

    gateway.md_api.login_status = False
    main_engine.event_engine.emit(
        gateway_manager_module.EVENT_LOG,
        SimpleNamespace(msg="行情服务器连接断开", gateway_name="CTP"),
    )

    state = manager.get_status()["ctp"]
    assert state.status == GatewayStatus.CONNECTING
    assert state.reconnect_attempts == 1
    assert FakeTimer.created[0].delay == 1.0

    FakeTimer.created[0].fire()
    assert main_engine.connect_calls[-1][1] == "CTP"

    with manager._condition:
        manager._cancel_reconnect_timer_locked("ctp")
        manager.states["ctp"].reconnect_attempts = 3
        manager._schedule_reconnect_locked("ctp")
        assert manager.states["ctp"].status == GatewayStatus.ERROR
        assert "上限" in manager.states["ctp"].last_error
