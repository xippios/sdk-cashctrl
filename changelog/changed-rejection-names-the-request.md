- Two errors that the client words from CashCtrl's answers name the request by its method
  and path, as xippios-core's `request_description` gives it and sdk-core's conventions §5
  ask: a refusal sent as HTTP 200, `RequestRejected`, after the fields or upstream's
  message, and the `ValidationError` of a file task whose answer is JSON but no refusal. A
  refused journal entry reads `CashCtrl rejected the request: debitId: This field cannot be empty. (POST /api/v1/journal/create.json)`,
  where it read `CashCtrl rejected the request: debitId: This field cannot be empty.`, in the
  exception's message, in a tool's answer after `error: RequestRejected:` and in a route's
  problem `detail`, and an export's stray JSON reads `CashCtrl: the answer is JSON that is neither a file nor a refusal; nothing was written (GET /api/v1/account/list.pdf)`,
  where it read `cashctrl: account/list.pdf answered JSON that is neither a file nor a refusal; nothing was written`.
  The classes, their bases, their statuses and every attribute stay, and a
  `RequestRejected` built without the new keyword `request` names no request, as before.
  (https://github.com/xippios/sdk-cashctrl/issues/117)
