// SPDX-License-Identifier: Proprietary
// Copyright 2026-present Citi MLOps Plane. All rights reserved.

const EXTERNAL_URL_RE = /^https?:\/\//;

export function ReadMore({ href = "#" }: { href?: string }) {
  const isExternal = EXTERNAL_URL_RE.test(href);
  return (
    <a
      href={href}
      target={isExternal ? "_blank" : undefined}
      rel={isExternal ? "noopener noreferrer" : undefined}
      onClick={(e) => {
        if (href === "#") e.preventDefault();
      }}
      className="text-primary underline underline-offset-2 hover:text-primary/80"
    >
      Read more
    </a>
  );
}
