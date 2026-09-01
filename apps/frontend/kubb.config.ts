import { defineConfig } from "@kubb/core";
import { pluginOas } from "@kubb/plugin-oas";
import { pluginTs } from "@kubb/plugin-ts";
import { pluginClient } from "@kubb/plugin-client";

// Reads the OpenAPI spec exported by the FastAPI backend (single source of truth,
// see specs/README.md) and generates a fully-typed fetch client + TS types.
export default defineConfig({
  root: ".",
  input: {
    path: "../../packages/api-spec/openapi.json",
  },
  output: {
    path: "src/api/generated",
    clean: true,
  },
  plugins: [
    pluginOas({}),
    pluginTs({
      output: { path: "types" },
    }),
    pluginClient({
      output: { path: "clients" },
      importPath: "@/api/client",
    }),
  ],
});
