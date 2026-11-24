- Thirteen fields that upstream sends with a time of day are naive `datetime` values, where
  they were dates cut from it: a fiscal period's `start`, `end`, `salary_start` and
  `salary_end`, a tax rate's `date_valid`, a journal entry's `date_added`, `start_date` and
  `end_date`, a person's `date_birth`, an order's `date`, `start_date` and `end_date`, and a
  book entry's `date`. A fiscal period's `end` reads `2025-12-31T23:59:59` where it read
  `2025-12-31`, and a write still sends the date alone.
  (https://github.com/xippios/sdk-cashctrl/issues/141)
