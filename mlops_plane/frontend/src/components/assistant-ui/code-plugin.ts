// SPDX-License-Identifier: Proprietary
// Copyright 2026-present Citi MLOps Plane. All rights reserved.

import {
  createCodePlugin as createShikiCodePlugin,
  type CodeHighlighterPlugin,
  type CodePluginOptions,
  type HighlightOptions,
  type HighlightResult,
} from "@streamdown/code";
import type { BundledLanguage } from "shiki";

// Fence tags LLMs/users commonly write that shiki doesn't expose as aliases.
// Keys are lower-cased input; values are canonical shiki language ids.
const LANGUAGE_ALIAS_OVERRIDES: Record<string, BundledLanguage> = {
  objectivec: "objective-c",
  "obj-c": "objective-c",
  objectivecpp: "objective-cpp",
  "objective-cplusplus": "objective-cpp",
  objcpp: "objective-cpp",
  "c++": "cpp",
  cplusplus: "cpp",
  "c#": "csharp",
  cs: "csharp",
  "f#": "fsharp",
  "c-sharp": "csharp",
  "f-sharp": "fsharp",
  golang: "go",
  rs: "rust",
  rb: "ruby",
  py: "python",
  sh: "shellscript",
  bash: "shellscript",
  zsh: "shellscript",
  shell: "shellscript",
  yml: "yaml",
  ts: "typescript",
  js: "javascript",
  kt: "kotlin",
  rsx: "rust",
  "vue-html": "vue",
};

const normalizeLanguage = (language: string): BundledLanguage => {
  const key = language.trim().toLowerCase();
  const override = LANGUAGE_ALIAS_OVERRIDES[key];
  return (override ?? (key as BundledLanguage));
};

export function createCodePlugin(
  options: CodePluginOptions = {},
): CodeHighlighterPlugin {
  const inner = createShikiCodePlugin(options);
  return {
    ...inner,
    supportsLanguage: (language) => inner.supportsLanguage(normalizeLanguage(language)),
    highlight: (
      opts: HighlightOptions,
      callback?: (result: HighlightResult) => void,
    ) =>
      inner.highlight(
        { ...opts, language: normalizeLanguage(opts.language) },
        callback,
      ),
  };
}
