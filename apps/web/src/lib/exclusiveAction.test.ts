import { expect, it, vi } from "vitest";
import { createExclusiveAction } from "./exclusiveAction";

it("sends only one write while a slow save is outstanding", async () => {
  const run = createExclusiveAction();
  let resolve!: (result: boolean) => void;
  const save = vi.fn(() => new Promise<boolean>(done => { resolve = done; }));
  const first = run(save);
  expect(await run(save)).toBe(false);
  expect(save).toHaveBeenCalledTimes(1);
  resolve(true);
  expect(await first).toBe(true);
});

it("permits retry after a failed write", async () => {
  const run = createExclusiveAction();
  await expect(run(async () => { throw new Error("offline"); })).rejects.toThrow("offline");
  expect(await run(async () => true)).toBe(true);
});
