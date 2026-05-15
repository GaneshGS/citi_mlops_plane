// SPDX-License-Identifier: Proprietary
// Copyright 2026-present Citi MLOps Plane. All rights reserved.

import type { ReactNode } from "react";

export function SettingsSection({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children: ReactNode;
}) {
  return (
    <section className="flex flex-col">
      <div className="mb-1 flex flex-col gap-0.5">
        <h2 className="text-base font-semibold font-heading text-foreground">
          {title}
        </h2>
        {description ? (
          <p className="text-xs text-muted-foreground leading-relaxed">
            {description}
          </p>
        ) : null}
      </div>
      <div className="flex flex-col divide-y divide-border/60">{children}</div>
    </section>
  );
}
