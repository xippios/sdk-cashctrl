- Adopts sdk-template v0.4.0, from v0.3.4, with `core_version=0.4.0`, `live_secrets=[CASHCTRL_DEMO_SUBDOMAIN]`, `api_key_location=basic`.
  The package depends on `xippios-core~=0.4.0`, whose tenant kit replaces the package's
  copies, and follows conventions 1.28. The answers `write_server=true`, `tenant_param=org`
  and `has_reference_data=false` render its two servers, their `--org` binding and the
  live run's key, and no reference scaffold.
  (https://github.com/xippios/sdk-template/releases/tag/v0.4.0, https://github.com/xippios/sdk-cashctrl/issues/112,
  https://github.com/xippios/sdk-cashctrl/issues/105)
