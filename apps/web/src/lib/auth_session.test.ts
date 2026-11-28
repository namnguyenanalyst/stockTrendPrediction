import { afterEach, describe, expect, it, vi } from "vitest";
import {
  getAuthToken,
  getUserPresets,
  getUserWatchlists,
  logoutUser,
  refreshToken,
  setAuthToken,
  setOnSessionExpired,
  setOnTokenRefreshed,
} from "./api";

afterEach(() => {
  setAuthToken(null);
  setOnTokenRefreshed(null);
  setOnSessionExpired(null);
  vi.unstubAllGlobals();
});

describe("Rotating backend sessions", () => {
  it("shares simultaneous refresh requests for the same cookie", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ access_token: "new-token" }) });
    vi.stubGlobal("fetch", fetchMock);
    const [first, second] = await Promise.all([refreshToken(), refreshToken()]);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(first.access_token).toBe(second.access_token);
  });

  it("revokes the rotated cookie after an outstanding refresh settles", async () => {
    let complete!: (response: Response) => void;
    const fetchMock = vi.fn()
      .mockImplementationOnce(() => new Promise<Response>((resolve) => { complete = resolve; }))
      .mockResolvedValueOnce({ ok: true, status: 204 });
    vi.stubGlobal("fetch", fetchMock);
    setAuthToken("old-token");
    const refreshing = refreshToken();
    const loggingOut = logoutUser();
    expect(getAuthToken()).toBeNull();
    expect(fetchMock).toHaveBeenCalledTimes(1);
    complete({ ok: true, json: async () => ({ access_token: "late-token" }) } as Response);
    await Promise.all([refreshing, loggingOut]);
    expect(getAuthToken()).toBeNull();
    expect(fetchMock).toHaveBeenLastCalledWith(
      "http://localhost:8000/api/v1/auth/logout", expect.objectContaining({ method: "POST" })
    );
  });

  it("clears local credentials even when revocation fails", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
    setAuthToken("old-token");
    await expect(logoutUser()).rejects.toThrow("offline");
    expect(getAuthToken()).toBeNull();
  });

  it("auto-refreshes once on 401 and retries concurrent requests with a single refresh call", async () => {
    const onRefreshed = vi.fn();
    setOnTokenRefreshed(onRefreshed);
    setAuthToken("expired-token");

    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/api/v1/auth/refresh")) {
        return { ok: true, status: 200, json: async () => ({ access_token: "fresh-token", token_type: "bearer" }) } as Response;
      }
      const authHeader = (init?.headers as Record<string, string>)?.Authorization;
      if (authHeader === "Bearer expired-token") {
        return { ok: false, status: 401, text: async () => JSON.stringify({ detail: "Token has expired" }) } as Response;
      }
      return { ok: true, status: 200, json: async () => [{ id: "1", name: "ok" }] } as Response;
    });
    vi.stubGlobal("fetch", fetchMock);

    const [watchlists, presets] = await Promise.all([getUserWatchlists(), getUserPresets()]);
    expect(watchlists).toHaveLength(1);
    expect(presets).toHaveLength(1);
    const refreshCalls = fetchMock.mock.calls.filter(([u]) => String(u).endsWith("/api/v1/auth/refresh"));
    expect(refreshCalls).toHaveLength(1);
    expect(onRefreshed).toHaveBeenCalledWith("fresh-token");
    expect(getAuthToken()).toBe("fresh-token");
  });

  it("clears session and invokes onSessionExpired when auto-refresh fails", async () => {
    const onExpired = vi.fn();
    setOnSessionExpired(onExpired);
    setAuthToken("expired-token");

    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/api/v1/auth/refresh")) {
        return { ok: false, status: 401, text: async () => JSON.stringify({ detail: "Refresh expired" }) } as Response;
      }
      return { ok: false, status: 401, text: async () => JSON.stringify({ detail: "Token has expired" }) } as Response;
    });
    vi.stubGlobal("fetch", fetchMock);

    await expect(getUserWatchlists()).rejects.toThrow("API error (401)");
    expect(getAuthToken()).toBeNull();
    expect(onExpired).toHaveBeenCalledTimes(1);
  });
});
