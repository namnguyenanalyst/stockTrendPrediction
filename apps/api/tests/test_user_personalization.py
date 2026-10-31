"""Unit & Integration tests cho Router Cá nhân hóa (/api/v1/user) và Cô lập Đa người dùng."""

import uuid

import httpx
import pytest


async def _register_and_login(client: httpx.AsyncClient, name_prefix: str) -> tuple[dict, str]:
    """Helper đăng ký và đăng nhập, trả về user data và Bearer token."""
    uid = uuid.uuid4().hex[:8]
    email = f"{name_prefix}_{uid}@quant.vn"
    pwd = "StrongPassword@123"
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": pwd, "full_name": f"User {name_prefix}"},
    )
    assert reg_res.status_code == 201
    user_data = reg_res.json()

    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": pwd},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    return user_data, token


# =============================================================================
# 1. Watchlists CRUD
# =============================================================================


@pytest.mark.asyncio
async def test_watchlist_create_and_list(async_client: httpx.AsyncClient):
    """Tạo mới và lấy danh sách watchlists của người dùng."""
    _, token = await _register_and_login(async_client, "wl_user")
    headers = {"Authorization": f"Bearer {token}"}

    # Tạo watchlist
    create_res = await async_client.post(
        "/api/v1/user/watchlists",
        json={"name": "VN30 Bluechips", "symbols": ["HPG", "VIC", "FPT"]},
        headers=headers,
    )
    assert create_res.status_code == 201
    created = create_res.json()
    assert created["name"] == "VN30 Bluechips"
    assert created["symbols"] == ["HPG", "VIC", "FPT"]
    assert "id" in created

    # Lấy danh sách
    list_res = await async_client.get("/api/v1/user/watchlists", headers=headers)
    assert list_res.status_code == 200
    items = list_res.json()
    assert len(items) == 1
    assert items[0]["id"] == created["id"]


@pytest.mark.asyncio
async def test_watchlist_validation_errors(async_client: httpx.AsyncClient):
    """Kiểm tra xác thực schema đầu vào cho watchlist (tên rỗng, symbols rỗng, sai kiểu)."""
    _, token = await _register_and_login(async_client, "val_user")
    headers = {"Authorization": f"Bearer {token}"}

    # Tên rỗng -> 422
    res_empty_name = await async_client.post(
        "/api/v1/user/watchlists",
        json={"name": "   ", "symbols": ["HPG"]},
        headers=headers,
    )
    assert res_empty_name.status_code == 422

    # Symbols rỗng -> 422
    res_empty_symbols = await async_client.post(
        "/api/v1/user/watchlists",
        json={"name": "Empty List", "symbols": []},
        headers=headers,
    )
    assert res_empty_symbols.status_code == 422

    # Symbols không phải mảng -> 422
    res_str_symbols = await async_client.post(
        "/api/v1/user/watchlists",
        json={"name": "String Symbol", "symbols": "HPG"},
        headers=headers,
    )
    assert res_str_symbols.status_code == 422


@pytest.mark.asyncio
async def test_watchlist_delete_and_double_delete(async_client: httpx.AsyncClient):
    """Xóa watchlist hợp lệ (204) và xóa lần 2 trả về 404."""
    _, token = await _register_and_login(async_client, "del_user")
    headers = {"Authorization": f"Bearer {token}"}

    create_res = await async_client.post(
        "/api/v1/user/watchlists",
        json={"name": "To Delete", "symbols": ["VIC"]},
        headers=headers,
    )
    wid = create_res.json()["id"]

    # Xóa lần 1 -> 204
    del1 = await async_client.delete(f"/api/v1/user/watchlists/{wid}", headers=headers)
    assert del1.status_code == 204

    # Xác nhận danh sách đã rỗng
    list_res = await async_client.get("/api/v1/user/watchlists", headers=headers)
    assert len(list_res.json()) == 0

    # Xóa lần 2 -> 404
    del2 = await async_client.delete(f"/api/v1/user/watchlists/{wid}", headers=headers)
    assert del2.status_code == 404


@pytest.mark.asyncio
async def test_watchlist_delete_invalid_uuid_returns_404(async_client: httpx.AsyncClient):
    """Xóa watchlist với ID không hợp lệ trả về 404."""
    _, token = await _register_and_login(async_client, "bad_id_user")
    headers = {"Authorization": f"Bearer {token}"}

    res = await async_client.delete("/api/v1/user/watchlists/not-a-valid-uuid", headers=headers)
    assert res.status_code == 404


# =============================================================================
# 2. Strategy Presets CRUD
# =============================================================================


@pytest.mark.asyncio
async def test_preset_create_and_list(async_client: httpx.AsyncClient):
    """Tạo mới và truy vấn mẫu tham số chiến lược."""
    _, token = await _register_and_login(async_client, "preset_user")
    headers = {"Authorization": f"Bearer {token}"}

    params = {"fast_period": 12, "slow_period": 26, "signal_period": 9}
    create_res = await async_client.post(
        "/api/v1/user/presets",
        json={
            "name": "MACD Classic",
            "description": "Standard MACD crossover",
            "parameters": params,
        },
        headers=headers,
    )
    assert create_res.status_code == 201
    created = create_res.json()
    assert created["name"] == "MACD Classic"
    assert created["parameters"] == params
    assert created["description"] == "Standard MACD crossover"

    list_res = await async_client.get("/api/v1/user/presets", headers=headers)
    assert list_res.status_code == 200
    assert any(p["id"] == created["id"] for p in list_res.json())


@pytest.mark.asyncio
async def test_preset_validation_errors(async_client: httpx.AsyncClient):
    """Kiểm tra lỗi xác thực cho preset (thiếu params, params sai kiểu)."""
    _, token = await _register_and_login(async_client, "pval_user")
    headers = {"Authorization": f"Bearer {token}"}

    # Thiếu parameters -> 422
    res_no_params = await async_client.post(
        "/api/v1/user/presets",
        json={"name": "NoParams"},
        headers=headers,
    )
    assert res_no_params.status_code == 422

    # Parameters không phải dict -> 422
    res_bad_params = await async_client.post(
        "/api/v1/user/presets",
        json={"name": "BadParams", "parameters": 12345},
        headers=headers,
    )
    assert res_bad_params.status_code == 422


@pytest.mark.asyncio
async def test_preset_delete_and_not_found(async_client: httpx.AsyncClient):
    """Xóa preset thành công (204) và xóa ID không tồn tại trả về 404."""
    _, token = await _register_and_login(async_client, "pdel_user")
    headers = {"Authorization": f"Bearer {token}"}

    create_res = await async_client.post(
        "/api/v1/user/presets",
        json={"name": "Temp Preset", "parameters": {"stop_loss": 0.05}},
        headers=headers,
    )
    pid = create_res.json()["id"]

    del_res = await async_client.delete(f"/api/v1/user/presets/{pid}", headers=headers)
    assert del_res.status_code == 204

    fake_id = str(uuid.uuid4())
    not_found_res = await async_client.delete(f"/api/v1/user/presets/{fake_id}", headers=headers)
    assert not_found_res.status_code == 404


# =============================================================================
# 3. Backtest Histories CRUD
# =============================================================================


@pytest.mark.asyncio
async def test_backtest_save_and_list(async_client: httpx.AsyncClient):
    """Lưu trữ kết quả kiểm thử và truy vấn lịch sử."""
    _, token = await _register_and_login(async_client, "bt_user")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "symbol": "HPG",
        "strategy_name": "MACD Trend",
        "strategy_type": "macd_crossover",
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "initial_capital": 100_000_000.0,
        "total_return": 0.25,
        "sharpe_ratio": 1.7,
        "max_drawdown": -0.05,
        "win_rate": 0.65,
        "equity_curve": [{"date": "2023-01-01", "equity": 100_000_000.0}],
    }
    save_res = await async_client.post("/api/v1/user/backtests", json=payload, headers=headers)
    assert save_res.status_code == 201
    saved = save_res.json()
    assert saved["symbol"] == "HPG"
    assert saved["total_return"] == 0.25
    assert len(saved["equity_curve"]) == 1

    list_res = await async_client.get("/api/v1/user/backtests", headers=headers)
    assert list_res.status_code == 200
    assert any(b["id"] == saved["id"] for b in list_res.json())


@pytest.mark.asyncio
async def test_backtest_validation_errors(async_client: httpx.AsyncClient):
    """Lưu backtest với vốn âm hoặc thiếu trường bắt buộc trả về 422."""
    _, token = await _register_and_login(async_client, "bt_val_user")
    headers = {"Authorization": f"Bearer {token}"}

    # Vốn âm -> 422
    res_neg_capital = await async_client.post(
        "/api/v1/user/backtests",
        json={"symbol": "HPG", "initial_capital": -100_000.0},
        headers=headers,
    )
    assert res_neg_capital.status_code == 422


# =============================================================================
# 4. Multi-Tenant Isolation & IDOR Prevention
# =============================================================================


@pytest.mark.asyncio
async def test_multi_tenant_isolation_user_a_and_user_b(async_client: httpx.AsyncClient):
    """User B không thể xem hoặc xóa tài nguyên của User A (ngăn ngừa IDOR)."""
    # Tạo User A
    _, token_a = await _register_and_login(async_client, "tenant_a")
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Tạo User B
    _, token_b = await _register_and_login(async_client, "tenant_b")
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A tạo Watchlist, Preset, Backtest
    wl_a = (
        await async_client.post(
            "/api/v1/user/watchlists",
            json={"name": "Alpha Watchlist A", "symbols": ["VIC", "VHM"]},
            headers=headers_a,
        )
    ).json()

    preset_a = (
        await async_client.post(
            "/api/v1/user/presets",
            json={"name": "Alpha Preset A", "parameters": {"k": 10}},
            headers=headers_a,
        )
    ).json()

    bt_a = (
        await async_client.post(
            "/api/v1/user/backtests",
            json={
                "symbol": "VIC",
                "strategy_name": "Strat A",
                "strategy_type": "sma",
                "start_date": "2023-01-01",
                "end_date": "2023-12-31",
                "initial_capital": 50_000_000.0,
                "total_return": 0.12,
                "sharpe_ratio": 1.3,
                "max_drawdown": -0.04,
                "win_rate": 0.60,
                "equity_curve": [],
            },
            headers=headers_a,
        )
    ).json()

    # 1. User B liệt kê tài nguyên -> không thấy bất kỳ tài nguyên nào của User A
    b_watchlists = (await async_client.get("/api/v1/user/watchlists", headers=headers_b)).json()
    assert not any(w["id"] == wl_a["id"] for w in b_watchlists)

    b_presets = (await async_client.get("/api/v1/user/presets", headers=headers_b)).json()
    assert not any(p["id"] == preset_a["id"] for p in b_presets)

    b_backtests = (await async_client.get("/api/v1/user/backtests", headers=headers_b)).json()
    assert not any(b["id"] == bt_a["id"] for b in b_backtests)

    # 2. User B cố gắng xóa tài nguyên của User A -> trả về HTTP 404 (IDOR Prevention)
    del_wl_res = await async_client.delete(
        f"/api/v1/user/watchlists/{wl_a['id']}", headers=headers_b
    )
    assert del_wl_res.status_code == 404

    del_preset_res = await async_client.delete(
        f"/api/v1/user/presets/{preset_a['id']}", headers=headers_b
    )
    assert del_preset_res.status_code == 404

    # 3. Xác nhận tài nguyên của User A vẫn nguyên vẹn
    a_watchlists = (await async_client.get("/api/v1/user/watchlists", headers=headers_a)).json()
    assert any(w["id"] == wl_a["id"] for w in a_watchlists)

    a_presets = (await async_client.get("/api/v1/user/presets", headers=headers_a)).json()
    assert any(p["id"] == preset_a["id"] for p in a_presets)


@pytest.mark.asyncio
async def test_unauthenticated_access_denied_401(async_client: httpx.AsyncClient):
    """Mọi truy cập chưa xác thực vào endpoint cá nhân hóa đều bị từ chối 401."""
    assert (await async_client.get("/api/v1/user/watchlists")).status_code == 401
    assert (
        await async_client.post("/api/v1/user/watchlists", json={"name": "x", "symbols": ["VIC"]})
    ).status_code == 401
    assert (
        await async_client.delete(f"/api/v1/user/watchlists/{uuid.uuid4()}")
    ).status_code == 401

    assert (await async_client.get("/api/v1/user/presets")).status_code == 401
    assert (
        await async_client.post("/api/v1/user/presets", json={"name": "x", "parameters": {}})
    ).status_code == 401
    assert (await async_client.delete(f"/api/v1/user/presets/{uuid.uuid4()}")).status_code == 401

    assert (await async_client.get("/api/v1/user/backtests")).status_code == 401
    assert (
        await async_client.post("/api/v1/user/backtests", json={"symbol": "VIC"})
    ).status_code == 401
