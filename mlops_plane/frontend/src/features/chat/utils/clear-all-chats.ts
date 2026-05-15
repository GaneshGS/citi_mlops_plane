// SPDX-License-Identifier: Proprietary
// Copyright 2026-present Citi MLOps Plane. All rights reserved.

import { db } from "../db";

export async function countAllChats(): Promise<number> {
  return db.threads.count();
}

export async function clearAllChats(): Promise<void> {
  await db.transaction("rw", db.threads, db.messages, async () => {
    await db.messages.clear();
    await db.threads.clear();
  });
}
