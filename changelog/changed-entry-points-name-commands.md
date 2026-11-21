- Each entry point names itself in its usage line and in an error of its command line,
  `xippios-cashctrl-mcp-read: error: ...`, where both named their servers,
  `xippios-cashctrl` and `xippios-cashctrl-write`. The help of `--allow-remote` says on the
  read server that it changes nothing, since that server is not held to loopback, and on
  the write server that it serves this write server beyond loopback.
  (https://github.com/xippios/sdk-core/issues/167)
