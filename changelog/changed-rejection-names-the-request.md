- A refusal that CashCtrl sends as HTTP 200, `RequestRejected`, names the request by its
  method and path after the fields or upstream's message, as xippios-core's
  `request_description` gives it and sdk-core's conventions §5 ask. A refused journal entry
  reads `CashCtrl rejected the request: debitId: This field cannot be empty. (POST /api/v1/journal/create.json)`,
  where it read `CashCtrl rejected the request: debitId: This field cannot be empty.`, in the
  exception's message, in a tool's answer after `error: RequestRejected:` and in a route's
  problem `detail`. The class, its base, the status 422 and every attribute stay, and a
  `RequestRejected` built without the new keyword `request` names no request, as before.
  (https://github.com/xippios/sdk-cashctrl/issues/117)
