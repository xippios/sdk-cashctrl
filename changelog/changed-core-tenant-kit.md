- The organisation registry, `list_organisations`, the `--org` lock and its serve command
  are xippios-core's again, `Tenants`, `list_task`, `TenantLock` and `serve_tenants`, in
  place of the package's copies: `--org`, its help, its startup checks and the bound
  server's instructions are unchanged, and an error of an entry point's command line names
  the entry point, `xippios-cashctrl-mcp-read: error: ...`, where it named
  `xippios-cashctrl`. `_client.py` declares the variables the package reads as core's
  `EnvVar` entries, `ENV_VARS`, for a host.
  (https://github.com/xippios/sdk-core/issues/166,
  https://github.com/xippios/sdk-cashctrl/issues/61)
