Source: <https://app.cashctrl.com/static/help/en/api/index.html#intro>

## Introduction

The CashCtrl API is organized around REST. Our API has predictable resource-oriented URLs, accepts form-encoded request bodies, returns JSON-encoded responses, and uses standard HTTP response codes and authentication.

The API is only available to PRO users as it requires an API user for each organization you manage, more about that in the next section: Authentication.

To test the API you can clone your main organization into a test organization and create an API user there. To do this in CashCtrl, go to Settings → Organizations → Copy.

#### Base URL

```
https://myorg.cashctrl.com/api/v1
```

Note that `myorg` is the sub-domain of the organization you're accessing.
