- `get_fiscal_period` (`fiscalperiod/read.json`, the tool `cashctrl_get_fiscal_period`)
  reads one fiscal period by its `id`, or without one the API user's current period, the
  one the lists and balances answer for when given no `fiscal_period_id`. Its
  `is_current` comes back false even for the current period, as upstream sends it, and
  `list_fiscal_periods` marks the current one.
  (https://github.com/xippios/sdk-cashctrl/issues/53)
