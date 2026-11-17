- The fixture recorder sends a GET only to a path that the snapshot in `docs/upstream/`
  documents as a GET: a GET to a path documented as a POST, such as `account/create.json`
  or `order/bookentry/create.json`, or to a path the snapshot does not name, is refused
  before a request is sent, as a GET to the eleven write paths already was. The method
  comes from each operation's Endpoint block, so a refreshed snapshot moves the refusal
  with it. (https://github.com/xippios/sdk-cashctrl/issues/27)
