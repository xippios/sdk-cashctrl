- `xippios.cashctrl.mcp.build()` and `xippios.cashctrl.mcp_write.build()` return core's
  `ToolSet`, the tools a host serves as the entry point does, and take core's
  `TenantLock`, where they returned the server and took the package's own lock. A caller
  that built a server from `build()` passes the tool set to
  `xippios.core.mcp.build_server`, and `mcp.server` and `mcp_write.server` are the servers
  as before. (https://github.com/xippios/sdk-core/issues/245,
  https://github.com/xippios/sdk-core/issues/166)
