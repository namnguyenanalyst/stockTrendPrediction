import { afterEach, describe, expect, it, vi } from "vitest";
import { getAuthToken, logoutUser, refreshToken, setAuthToken } from "./api";

afterEach(() => {
  setAuthToken(null);
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
});
