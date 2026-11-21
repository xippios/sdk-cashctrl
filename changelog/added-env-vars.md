- `xippios.cashctrl.mcp.ENV_VARS` and `xippios.cashctrl.mcp_write.ENV_VARS` name the
  variables the package reads, as core's `EnvVar` entries: `CASHCTRL_ORGS`, then each
  organisation's `CASHCTRL_<NAME>_API_KEY` and `CASHCTRL_<NAME>_SUBDOMAIN`, both secret. A
  host reads them to configure the package without its documentation.
  (https://github.com/xippios/sdk-core/issues/245,
  https://github.com/xippios/sdk-template/issues/81)
