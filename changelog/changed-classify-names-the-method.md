- The two errors that `classify` words itself name the request by its method and path, as
  xippios-core's `request_description` gives it, where they named the path alone, as
  sdk-core's conventions §5 and its ADR-0030, decision 4, ask. An unknown id on a read
  reads `CashCtrl: This account does not exist. (GET /api/v1/account/read.json)`, where it
  read `CashCtrl: This account does not exist. (/account/read.json)`, and the 404 of an
  unknown id on a file path reads `CashCtrl: no record has an id asked, HTTP 404
  (GET /api/v1/report/element/download.pdf)`, where it read `CashCtrl: no record has an id
  asked, HTTP 404 (/report/element/download.pdf)`. The class, the status and every
  attribute stay. (https://github.com/xippios/sdk-cashctrl/issues/107)
