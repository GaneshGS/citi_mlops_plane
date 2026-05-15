// SPDX-License-Identifier: Proprietary
// Copyright 2026-present Citi MLOps Plane. All rights reserved.

import { AspectRatio as AspectRatioPrimitive } from "radix-ui";

function AspectRatio({
  ...props
}: React.ComponentProps<typeof AspectRatioPrimitive.Root>) {
  return <AspectRatioPrimitive.Root data-slot="aspect-ratio" {...props} />;
}

export { AspectRatio };
