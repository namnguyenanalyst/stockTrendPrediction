import { afterEach, it, expect, vi } from "vitest";
import { getUserPresets, updateUserPreset } from "./api";

afterEach(() => vi.unstubAllGlobals());

it("updates a preset in place with PUT, without deleting the old record", async () => {
  const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ id: "existing" }) });
  vi.stubGlobal("fetch", fetchMock);
  await updateUserPreset("existing", "Name", null, { status: "draft" });
  expect(fetchMock).toHaveBeenCalledTimes(1);
  expect(fetchMock).toHaveBeenCalledWith("http://localhost:8000/api/v1/user/presets/existing", expect.objectContaining({ method: "PUT" }));
});

it("loads subsequent pages so saved strategies after the first 100 remain visible", async () => {
  const fetchMock = vi.fn()
    .mockResolvedValueOnce({ ok: true, json: async () => Array.from({ length: 100 }, (_, i) => ({ id: String(i) })) })
    .mockResolvedValueOnce({ ok: true, json: async () => [{ id: "100" }] });
  vi.stubGlobal("fetch", fetchMock);
  expect(await getUserPresets()).toHaveLength(101);
  expect(fetchMock).toHaveBeenLastCalledWith("http://localhost:8000/api/v1/user/presets?limit=100&offset=100", expect.anything());
});
