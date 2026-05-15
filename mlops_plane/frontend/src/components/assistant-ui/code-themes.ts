// SPDX-License-Identifier: Proprietary
// Copyright 2026-present Citi MLOps Plane. All rights reserved.

import oneDarkPro from "@shikijs/themes/one-dark-pro";
import oneLight from "@shikijs/themes/one-light";
import type { ThemeRegistrationAny } from "shiki";

// Canonical Atom One Dark / One Light themes, shipped by `@shikijs/themes`.
// We only override the background so the code block blends into the app's
// `--code-block` surface instead of painting its own. Every token color and
// scope mapping is left intact — that's what gives consistent multi-language
// highlighting (including Objective-C, Go, Rust, etc.) out of the box.
const withTransparentBg = (theme: ThemeRegistrationAny): ThemeRegistrationAny => ({
  ...theme,
  bg: "transparent",
  colors: {
    ...theme.colors,
    "editor.background": "transparent",
  },
});

export const mlopsLightTheme: ThemeRegistrationAny = {
  ...withTransparentBg(oneLight),
  name: "mlops-light",
};

export const mlopsDarkTheme: ThemeRegistrationAny = {
  ...withTransparentBg(oneDarkPro),
  name: "mlops-dark",
};
