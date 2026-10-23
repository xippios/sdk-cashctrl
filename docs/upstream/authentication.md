Source: <https://app.cashctrl.com/static/help/en/api/index.html#auth>

## Authentication

The CashCtrl API uses API keys to authenticate requests. You can view and manage your API keys in CashCtrl under Settings → Users & Roles.

You have to create an API user for each organization that you would like to access. This means that an API user can only access one organization and has the permissions defined by the role you've assigned to the API user.

You can add a new API user under Settings → Users & Roles → Add → Add API user.

Your API keys carry many privileges, so be sure to keep them secure! Do not share your API keys in publicly accessible areas such as GitHub, client-side code, and so forth.

Authentication to the API is performed via HTTP Basic Auth. Provide your API key as the basic auth username value. You do not need to provide a password. This is done for every request, not just once.

All API requests must be made over HTTPS. Calls made over plain HTTP will fail. API requests without authentication will also fail.

#### Example

Retrieving the journal book entries list via curl:

```
curl https://myorg.cashctrl.com/api/v1/journal/list.json -u zjdqcZjsfSYyM4EPG19tHss6X5NIHf0b:
```

Note: Replace `zjdqcZjsfSYyM4EPG19tHss6X5NIHf0b` with your API key. The colon after the key prevents curl from asking for a password.
