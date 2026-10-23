Source: <https://app.cashctrl.com/static/help/en/api/index.html#lang>

## Language

Unlike a regular user an API user does not have user preferences with a defined language. Instead the desired language is sent with each request. Simply add the following request parameter: `lang` (e.g. lang=en).

Available languages: de, fr, it, en.

For most JSON requests the language won't matter as the response only contains data, and the data may contain all languages or more accurately the languages of the data that has been entered by the user. It matters mostly for error messages and generated PDFs, Excel sheets and CSV files which will come in one language only.

#### Example

Retrieving the annual report PDF in German via curl:

```
curl https://myorg.cashctrl.com/api/v1/report/collection/download_annualreport.pdf?lang=de -u zjdqcZjsfSYyM4EPG19tHss6X5NIHf0b:
```
