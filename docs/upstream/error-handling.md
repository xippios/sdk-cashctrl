Source: <https://app.cashctrl.com/static/help/en/api/index.html#errors>

## Error handling

CashCtrl uses conventional HTTP response codes to indicate the success or failure of an API request. In general: Codes in the 2xx range indicate success (except for validation errors). Codes in the 4xx range indicate an issue with the request, for example unauthorized, forbidden or not found. Codes in the 5xx range indicate an error with our servers (these are rare).

However, response codes are not used to indicate form validation errors (like a missing ID or incorrect date). Instead, you will get a HTTP 200 OK and the JSON response will contain a field named "success" which is either true or false. If false, there will be another field named "errors" which contains one or multiple errors, see example response.

#### HTTP status codes

| | |
| --- | --- |
| `200 - OK` | Everything worked as expected. However, form validation errors are still possible, see example response. |
| `401 - Unauthorized` | No valid API key provided. |
| `403 - Forbidden` | The API key doesn't have permissions to perform the request. |
| `404 - Not Found` | The requested endpoint doesn't exist. |
| `405 - Method Not Allowed` | The HTTP method (GET, POST, etc.) used is not allowed. |
| `418 - I'm a teapot` | Error you get when CashCtrl is a teapot and not a coffee pot. |
| `429 - Too Many Requests` | Too many requests hit the API too quickly. We recommend adding delays between your requests. For more information, see our [Terms of Service](https://cashctrl.com/en/about/terms). |
| `500, 502, 503, 504 - Server Errors` | Something went wrong on our end - not your fault. Please contact support. |

#### Example response

This is an example response with a HTTP status of 200 but containing form validation errors:

```
{
    "success": false,
    "errors": [
        {
            "field": "debitId",
            "message": "This field cannot be empty."
        },
        {
            "field": "creditId",
            "message": "This field cannot be empty."
        },
        {
            "field": "amount",
            "message": "This field cannot be empty."
        }
    ]
}
```
