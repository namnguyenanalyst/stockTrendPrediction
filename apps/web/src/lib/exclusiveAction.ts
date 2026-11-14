/** Serialize a single UI mutation; repeated activation cannot submit a second write. */
export function createExclusiveAction() {
  let pending = false;
  return async (action: () => Promise<boolean>): Promise<boolean> => {
    if (pending) return false;
    pending = true;
    try { return await action(); }
    finally { pending = false; }
  };
}
