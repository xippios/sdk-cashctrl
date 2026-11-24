- `download_persons` without `columns` sends none, so the file holds upstream's default
  columns, ten labels such as `Name` and `E-Mail Work`, none of them `ssn` or an `iban`,
  where it held the fields `list_persons` returns. Pass `columns=list(tasks.PERSON_COLUMNS)`
  for those fields. (https://github.com/xippios/sdk-cashctrl/issues/143)
