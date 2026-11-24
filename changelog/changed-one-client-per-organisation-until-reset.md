- An organisation's client is kept until `TENANTS.reset()`, so a changed subdomain or key
  takes effect at the next start, where a running server built a new client. A malformed
  subdomain is refused by the package's own `ConfigError`, which names the variable and the
  expected form and no value. (https://github.com/xippios/sdk-core/issues/475)
