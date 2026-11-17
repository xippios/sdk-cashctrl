- `list_cost_centers` takes `fiscal_period_id`, the fiscal period of the balances
  `opening_amount` and `end_amount`, and sends it as `fiscalPeriodId`, so `meta.request`
  names the period that answered. Left out, the balances are assumed to be the current
  period's, as before.
  (https://github.com/xippios/sdk-cashctrl/issues/24)
