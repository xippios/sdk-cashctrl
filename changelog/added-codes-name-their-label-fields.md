- A person's `language` and `country`, a person's `language_code` and a report tree node's
  `type` declare with core's `NamedBy` the field beside them that holds their name, so a check
  of the models finds each code beside its label. Answers are unchanged: the name stands on the
  record, and `meta.names` takes no entry for these codes.
  (sdk-core ADR-0067, https://github.com/xippios/sdk-cashctrl/issues/167)
