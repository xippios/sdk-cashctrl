Source: <https://app.cashctrl.com/static/help/en/api/index.html#/fiscalperiod>\
Fetched: 2026-10-23 (UTC)

## Fiscal period

The following API endpoints are for manipulating fiscal periods and salary periods. A fiscal period is simply a time period, usually a calendar year. All journal book entries (their dates) must be covered by a fiscal period and cannot be created outside of existing fiscal periods. So a fiscal period must first be created before book entries for that period can be created. Fiscal periods can be completed which locks the book entries in that period. Completed fiscal periods can be reopened anytime. Individual months can also be completed and reopened.

### Read fiscal period

Returns a single fiscal period by ID or the current fiscal period.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | optional, TEXT | The ID of the fiscal period. Leave empty to read the current fiscal period (see [Switch fiscal period](https://app.cashctrl.com/static/help/en/api/index.html#/fiscalperiod/switch.json)). |

#### Endpoint

```
GET /api/v1/fiscalperiod/read.json
```

### List fiscal periods

Returns a list of all fiscal periods.

#### Endpoint

```
GET /api/v1/fiscalperiod/list.json
```

### Create fiscal period

Creates a new manual fiscal period. Returns either a success or multiple error messages (for each issue).

#### Parameters

| | | |
| --- | --- | --- |
| `end` | optional, DATE | The end date of the fiscal period, if `isCustom` is set to true, ignored otherwise.<br>Format: YYYY-MM-DD. Example: `2020-01-15`. |
| `isCustom` | optional, BOOLEAN | If true, create a custom fiscal period with `start` and `end` date. `type` will be ignored. Defaults to false. Possible values: true, false. |
| `name` | optional, TEXT, MAX:30 | The name of the fiscal period, if `isCustom` is set to true, ignored otherwise. |
| `salaryEnd` | optional, DATE | The end date of the salary period, if `isCustom` is set to true, ignored otherwise.<br>Format: YYYY-MM-DD. Example: `2020-01-15`. |
| `salaryStart` | optional, DATE | The start date of the salary period, if `isCustom` is set to true, ignored otherwise.<br>Format: YYYY-MM-DD. Example: `2020-01-15`. |
| `start` | optional, DATE | The start date of the fiscal period, if `isCustom` is set to true, ignored otherwise.<br>Format: YYYY-MM-DD. Example: `2020-01-15`. |
| `type` | optional, TEXT | Creation type for creating a calendar year, if `isCustom` is not set. Either LATEST, which will create the next year after the latest existing year, or EARLIEST, which will create the year before the earliest existing year. Defaults to LATEST. Possible values: EARLIEST, LATEST. |

#### Endpoint

```
POST /api/v1/fiscalperiod/create.json
```

### Update fiscal period

Updates an existing fiscal period. Note that all parameters must be submitted, omitted parameters are treated as empty values. Returns either a success or multiple error messages (for each issue).

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the fiscal period to update. |
| `end` | optional, DATE | The end date of the fiscal period, if `isCustom` is set to true, ignored otherwise.<br>Format: YYYY-MM-DD. Example: `2020-01-15`. |
| `isCustom` | optional, BOOLEAN | If true, create a custom fiscal period with `start` and `end` date. `type` will be ignored. Defaults to false. Possible values: true, false. |
| `name` | optional, TEXT, MAX:30 | The name of the fiscal period, if `isCustom` is set to true, ignored otherwise. |
| `salaryEnd` | optional, DATE | The end date of the salary period, if `isCustom` is set to true, ignored otherwise.<br>Format: YYYY-MM-DD. Example: `2020-01-15`. |
| `salaryStart` | optional, DATE | The start date of the salary period, if `isCustom` is set to true, ignored otherwise.<br>Format: YYYY-MM-DD. Example: `2020-01-15`. |
| `start` | optional, DATE | The start date of the fiscal period, if `isCustom` is set to true, ignored otherwise.<br>Format: YYYY-MM-DD. Example: `2020-01-15`. |
| `type` | optional, TEXT | Creation type for creating a calendar year, if `isCustom` is not set. Either LATEST, which will create the next year after the latest existing year, or EARLIEST, which will create the year before the earliest existing year. Defaults to LATEST. Possible values: EARLIEST, LATEST. |

#### Endpoint

```
POST /api/v1/fiscalperiod/update.json
```

### Switch fiscal period

Switches the current fiscal period. Every user has a current fiscal period set, which is considered for various data responses like e.g. the list of journal entries. If you retrieve the list of journal entries, only the entries in the current fiscal period are returned. You have to use this API endpoint to switch the current fiscal period to another one.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |

#### Endpoint

```
POST /api/v1/fiscalperiod/switch.json
```

### Delete fiscal periods

Deletes one or multiple fiscal periods. Note that you cannot delete fiscal periods if there are book entries that are not covered by another fiscal period. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the selected entries, comma-separated. |

#### Endpoint

```
POST /api/v1/fiscalperiod/delete.json
```

### Get result

Get the result (profit or loss) of the given fiscal period.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | optional, NUMBER | The ID of the fiscal period. |

#### Endpoint

```
GET /api/v1/fiscalperiod/result
```

### List depreciations

List the depreciations on fixed assets to be booked in the current fiscal period (see [Switch fiscal period](https://app.cashctrl.com/static/help/en/api/index.html#/fiscalperiod/switch.json)). This doesn't actually book anything, see the next API endpoint for that.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |

#### Endpoint

```
GET /api/v1/fiscalperiod/depreciations.json
```

### Book depreciations

Book depreciations on fixed assets in the current fiscal period (see [Switch fiscal period](https://app.cashctrl.com/static/help/en/api/index.html#/fiscalperiod/switch.json)).

#### Parameters

| | | |
| --- | --- | --- |
| `depreciation` | mandatory, CSV | The IDs of fixed asset accounts to depreciate, comma-separated. See previous endpoint for a list of depreciable accounts. |
| `id` | mandatory, NUMBER | The ID of the fiscal period. |

#### Endpoint

```
POST /api/v1/fiscalperiod/bookdepreciations.json
```

### List currency exchange differences

List the currency exchange differences to be booked in the current fiscal period (see [Switch fiscal period](https://app.cashctrl.com/static/help/en/api/index.html#/fiscalperiod/switch.json)). These book entries make corrections to the main currency balance of accounts with a foreign currency. This doesn't actually book anything, see the next API endpoint for that.

#### Parameters

| | | |
| --- | --- | --- |
| `date` | optional, DATE | The booking date. Leave empty to use the last day of the fiscal period. If date is set, the fiscal period ID is ignored.<br>Format: YYYY-MM-DD. Example: `2020-01-15`. |
| `id` | optional, NUMBER | The ID of the fiscal period. Set either this or the `date`. |

#### Endpoint

```
GET /api/v1/fiscalperiod/exchangediff.json
```

### Book currency exchange differences

Book currency exchange differences in the current fiscal period (see [Switch fiscal period](https://app.cashctrl.com/static/help/en/api/index.html#/fiscalperiod/switch.json)). These book entries make corrections to the main currency balance of accounts with a foreign currency.

#### Parameters

<table>
<tr><th><code>exchangeDiff</code></th><td>mandatory, JSON</td><td>The exchange differences to book.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>accountId</code></th><td>mandatory, NUMBER</td><td>The ID of the account in a foreign currency.</td></tr>
<tr><th><code>currencyRate</code></th><td>mandatory, NUMBER</td><td>The final exchange rate to use (by which the main currency amount will be corrected).</td></tr>
</table>
</td></tr>
<tr><th><code>date</code></th><td>optional, DATE</td><td>The booking date. Leave empty to use the last day of the fiscal period. If date is set, the fiscal period ID is ignored.<br>Format: YYYY-MM-DD. Example: <code>2020-01-15</code>.</td></tr>
<tr><th><code>id</code></th><td>optional, NUMBER</td><td>The ID of the fiscal period. Set either this or the <code>date</code>.</td></tr>
</table>

#### Endpoint

```
POST /api/v1/fiscalperiod/bookexchangediff.json
```

### Complete fiscal period

Completes the fiscal period. This action locks the book entries in this period so they cannot be manipulated anymore. However, you can reopen the fiscal period any time, see next API endpoint.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the fiscal period to complete. |
| `isSalary` | optional, BOOLEAN | Complete the salary period instead of the fiscal period? Defaults to false. Possible values: true, false. |

#### Endpoint

```
POST /api/v1/fiscalperiod/complete.json
```

### Reopen fiscal period

Reopens the fiscal period. This unlocks the book entries in this period so they can be manipulated again.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the fiscal period to reopen. |
| `isSalary` | optional, BOOLEAN | Complete the salary period instead of the fiscal period? Defaults to false. Possible values: true, false. |

#### Endpoint

```
POST /api/v1/fiscalperiod/reopen.json
```

### Complete months

Completes the given months. This action locks the book entries in this period so they cannot be manipulated anymore. However, you can reopen those months any time, see next API endpoint.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the fiscal period to update. |
| `isSalary` | optional, BOOLEAN | Update the months for the salary period instead of the fiscal period? Defaults to false. Possible values: true, false. |
| `months` | optional, JSON | List of months to close and protect from changes. As as consequence, all other months not listed here within the same fiscal period stay open or become reopened. This is a JSON array of month identifiers. Example month identifier: "2022-03". Example array: ["2022-01", "2022-02", "2022-03"] = This would close Jan,Feb,Mar of 2022, but leave Apr,May,Jun,Jul,Aug,Sep,Oct,Nov open. |

#### Endpoint

```
POST /api/v1/fiscalperiod/complete_months.json
```

### Reopen months

Reopens the given months. This unlocks the book entries in this period so they can be manipulated again.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the fiscal period to update. |
| `isSalary` | optional, BOOLEAN | Update the months for the salary period instead of the fiscal period? Defaults to false. Possible values: true, false. |
| `months` | optional, JSON | List of months to close and protect from changes. As as consequence, all other months not listed here within the same fiscal period stay open or become reopened. This is a JSON array of month identifiers. Example month identifier: "2022-03". Example array: ["2022-01", "2022-02", "2022-03"] = This would close Jan,Feb,Mar of 2022, but leave Apr,May,Jun,Jul,Aug,Sep,Oct,Nov open. |

#### Endpoint

```
GET /api/v1/fiscalperiod/reopen_months.json
```

## Fiscal period task

The following API endpoints are for manipulating tasks, which appear in the fiscal period completion dialog.

### List tasks

Returns a list of tasks.

#### Endpoint

```
GET /api/v1/fiscalperiod/task/list.json
```

### Create task

Creates a new task. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `name` | mandatory, TEXT | The name/text of the task. |

#### Endpoint

```
POST /api/v1/fiscalperiod/task/create.json
```

### Delete tasks

Deletes one or multiple tasks. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the selected entries, comma-separated. |

#### Endpoint

```
POST /api/v1/fiscalperiod/task/delete.json
```

## Location

The following API endpoints are for managing locations. An organization can have multiple locations (e.g. headquarters, branches, warehouses) with each an address, logo, bank data, UID, etc.

### Read location

Returns a single location by ID.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |

#### Endpoint

```
GET /api/v1/location/read.json
```

### List locations

Returns a list of all locations.

#### Endpoint

```
GET /api/v1/location/list.json
```

### Create location

Creates a new location. Returns either a success or multiple error messages (for each issue).

#### Parameters

| | | |
| --- | --- | --- |
| `name` | mandatory, TEXT, MAX:250 | A name to describe and identify the location. Not used in an address, just for identification. |
| `address` | optional, TEXT, MAX:250 | The address (street, house number, additional info) of the location. Can contain multiple lines. |
| `bankAccountId` | optional, NUMBER | The ID of the bank account associated with this location. |
| `burNr` | optional, TEXT, MAX:32 | The BUR number (Business and Enterprise Register in Switzerland) of the company. |
| `canton` | optional, TEXT | The canton of the location (Switzerland only). Possible values: AG, AI, AR, BE, BL, BS, FR, GE, GL, GR, JU, LU, NE, NW, OW, SG, SH, SO, SZ, TG, TI, UR, VD, VS, ZG, ZH. |
| `city` | optional, TEXT, MAX:100 | The town / city of the location. |
| `country` | optional, TEXT | The country of the location. This is a country code with 3 characters (ISO 3166-1 alpha-3). Possible values: AFG, ALA, ALB, DZA, ASM, AND, AGO, AIA, ATG, ARG, ARM, ABW, AUS, AUT, AZE, BHS, BHR, BGD, BRB, BLR, BEL, BLZ, BEN, BMU, BTN, BOL, BES, BIH, BWA, BVT, BRA, IOT, BRN, BGR, BFA, BDI, KHM, CMR, CAN, CPV, CYM, CAF, TCD, CHL, CHN, CXR, CCK, COL, COM, COG, COK, CRI, CIV, HRV, CUB, CUW, CYP, CZE, DNK, DJI, DOM, DMA, ECU, EGY, SLV, GNQ, ERI, EST, ETH, FLK, FRO, FJI, FIN, FRA, GUF, GUY, PYF, GAB, GMB, GEO, DEU, GHA, GIB, GRC, GRL, GRD, GLP, GUM, GTM, GGY, GNB, GIN, HTI, HMD, VAT, HND, HKG, HUN, IND, IDN, IRN, IRQ, IRL, IMN, ISR, ITA, JAM, JPN, JEY, JOR, KAZ, KEN, KIR, PRK, KOR, KWT, KGZ, LAO, LVA, LBN, LSO, LBR, LBY, LIE, LTU, LUX, MAC, MKD, MDG, MWI, MYS, MDV, SOM, MLI, MLT, MHL, MTQ, MRT, MUS, MYT, MEX, FSM, MDA, MCO, MNG, MNE, MSR, MAR, MOZ, MMR, NAM, NRU, NPL, NLD, NCL, NZL, NIC, NGA, NER, NIU, NFK, MNP, NOR, OMN, PAK, PLW, PSE, PAN, PNG, PRY, PER, PHL, PCN, POL, PRT, PRI, QAT, REU, ROU, RUS, RWA, BLM, SHN, KNA, LCA, MAF, SPM, VCT, WSM, SMR, STP, SAU, SEN, SRB, SYC, SLE, SGP, SXM, SVK, SVN, SLB, ZAF, SGS, SSD, ESP, LKA, SDN, SUR, SJM, SWZ, SWE, CHE, SYR, TWN, TJK, TZA, THA, TLS, TGO, TKL, TON, TTO, TUN, TUR, TKM, TCA, TUV, UGA, UKR, ARE, GBR, USA, URY, UZB, VUT, VEN, VNM, VIR, VGB, WLF, YEM, ZMB, ZWE, ISL. |
| `email` | optional, TEXT, MAX:100 | The main e-mail address to contact the company. |
| `footer` | optional, TEXT | Footer text to display on order documents. See [Order](https://app.cashctrl.com/static/help/en/api/index.html#/order).<br>This can contain limited HTML for styling. Allowed tags: a, p, div, h1, h2, h3, h4, h5, h6, ul, ol, li, blockquote, b, i, s, u, o, sup, sub, ins, del, strong, strike, tt, code, big, small, br, span, em. Allowed inline CSS rules: background, background-color, color, font, font-size, font-weight, font-style, text-align, text-indent, text-decoration. |
| `isInactive` | optional, BOOLEAN | Mark the location as inactive. Inactive locations are greyed out and are no longer suggested. Possible values: true, false. |
| `logoFileId` | optional, NUMBER | The company logo. Supported types: JPG, GIF, PNG. Max. size: 400KB. Max. resolution: 2500x2500px. Use the [File API](https://app.cashctrl.com/static/help/en/api/index.html#/file) to upload a file and then use the file ID here. |
| `orgName` | optional, TEXT, MAX:250 | The name of the company. |
| `phoneMain` | optional, TEXT, MAX:100 | The main phone number to contact the company. |
| `phoneSalaryCert` | optional, TEXT, MAX:100 | The company's phone number written on the salary certificate. |
| `type` | optional, TEXT | The type of location. Defaults to MAIN (= company headquarters). Possible values: MAIN, BRANCH, STORAGE, OTHER. |
| `url` | optional, TEXT, MAX:100 | The company's website URL. |
| `vatUid` | optional, TEXT, MAX:32 | The UID (VAT no.) of the company. |
| `zip` | optional, TEXT, MAX:10 | The postal code of the location. |

#### Endpoint

```
POST /api/v1/location/create.json
```

### Update location

Updates an existing location. Note that all parameters must be submitted, omitted parameters are treated as empty values. Returns either a success or multiple error messages (for each issue).

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the location to update. |
| `name` | mandatory, TEXT, MAX:250 | A name to describe and identify the location. Not used in an address, just for identification. |
| `address` | optional, TEXT, MAX:250 | The address (street, house number, additional info) of the location. Can contain multiple lines. |
| `bankAccountId` | optional, NUMBER | The ID of the bank account associated with this location. |
| `burNr` | optional, TEXT, MAX:32 | The BUR number (Business and Enterprise Register in Switzerland) of the company. |
| `canton` | optional, TEXT | The canton of the location (Switzerland only). Possible values: AG, AI, AR, BE, BL, BS, FR, GE, GL, GR, JU, LU, NE, NW, OW, SG, SH, SO, SZ, TG, TI, UR, VD, VS, ZG, ZH. |
| `city` | optional, TEXT, MAX:100 | The town / city of the location. |
| `country` | optional, TEXT | The country of the location. This is a country code with 3 characters (ISO 3166-1 alpha-3). Possible values: AFG, ALA, ALB, DZA, ASM, AND, AGO, AIA, ATG, ARG, ARM, ABW, AUS, AUT, AZE, BHS, BHR, BGD, BRB, BLR, BEL, BLZ, BEN, BMU, BTN, BOL, BES, BIH, BWA, BVT, BRA, IOT, BRN, BGR, BFA, BDI, KHM, CMR, CAN, CPV, CYM, CAF, TCD, CHL, CHN, CXR, CCK, COL, COM, COG, COK, CRI, CIV, HRV, CUB, CUW, CYP, CZE, DNK, DJI, DOM, DMA, ECU, EGY, SLV, GNQ, ERI, EST, ETH, FLK, FRO, FJI, FIN, FRA, GUF, GUY, PYF, GAB, GMB, GEO, DEU, GHA, GIB, GRC, GRL, GRD, GLP, GUM, GTM, GGY, GNB, GIN, HTI, HMD, VAT, HND, HKG, HUN, IND, IDN, IRN, IRQ, IRL, IMN, ISR, ITA, JAM, JPN, JEY, JOR, KAZ, KEN, KIR, PRK, KOR, KWT, KGZ, LAO, LVA, LBN, LSO, LBR, LBY, LIE, LTU, LUX, MAC, MKD, MDG, MWI, MYS, MDV, SOM, MLI, MLT, MHL, MTQ, MRT, MUS, MYT, MEX, FSM, MDA, MCO, MNG, MNE, MSR, MAR, MOZ, MMR, NAM, NRU, NPL, NLD, NCL, NZL, NIC, NGA, NER, NIU, NFK, MNP, NOR, OMN, PAK, PLW, PSE, PAN, PNG, PRY, PER, PHL, PCN, POL, PRT, PRI, QAT, REU, ROU, RUS, RWA, BLM, SHN, KNA, LCA, MAF, SPM, VCT, WSM, SMR, STP, SAU, SEN, SRB, SYC, SLE, SGP, SXM, SVK, SVN, SLB, ZAF, SGS, SSD, ESP, LKA, SDN, SUR, SJM, SWZ, SWE, CHE, SYR, TWN, TJK, TZA, THA, TLS, TGO, TKL, TON, TTO, TUN, TUR, TKM, TCA, TUV, UGA, UKR, ARE, GBR, USA, URY, UZB, VUT, VEN, VNM, VIR, VGB, WLF, YEM, ZMB, ZWE, ISL. |
| `email` | optional, TEXT, MAX:100 | The main e-mail address to contact the company. |
| `footer` | optional, TEXT | Footer text to display on order documents. See [Order](https://app.cashctrl.com/static/help/en/api/index.html#/order).<br>This can contain limited HTML for styling. Allowed tags: a, p, div, h1, h2, h3, h4, h5, h6, ul, ol, li, blockquote, b, i, s, u, o, sup, sub, ins, del, strong, strike, tt, code, big, small, br, span, em. Allowed inline CSS rules: background, background-color, color, font, font-size, font-weight, font-style, text-align, text-indent, text-decoration. |
| `isInactive` | optional, BOOLEAN | Mark the location as inactive. Inactive locations are greyed out and are no longer suggested. Possible values: true, false. |
| `logoFileId` | optional, NUMBER | The company logo. Supported types: JPG, GIF, PNG. Max. size: 400KB. Max. resolution: 2500x2500px. Use the [File API](https://app.cashctrl.com/static/help/en/api/index.html#/file) to upload a file and then use the file ID here. |
| `orgName` | optional, TEXT, MAX:250 | The name of the company. |
| `phoneMain` | optional, TEXT, MAX:100 | The main phone number to contact the company. |
| `phoneSalaryCert` | optional, TEXT, MAX:100 | The company's phone number written on the salary certificate. |
| `type` | optional, TEXT | The type of location. Defaults to MAIN (= company headquarters). Possible values: MAIN, BRANCH, STORAGE, OTHER. |
| `url` | optional, TEXT, MAX:100 | The company's website URL. |
| `vatUid` | optional, TEXT, MAX:32 | The UID (VAT no.) of the company. |
| `zip` | optional, TEXT, MAX:10 | The postal code of the location. |

#### Endpoint

```
POST /api/v1/location/update.json
```

### Delete locations

Deletes one or multiple locations. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the selected entries, comma-separated. |

#### Endpoint

```
POST /api/v1/location/delete.json
```

## Organization

The following API endpoints are for reading organization (aka domain) related information. Please understand that we currently do not allow creation or manipulation of organizations via the API.

### Get logo

Returns the logo image of the organization (if set) or a one pixel invisible image if not set. The content type is that of the uploaded logo image (PNG, GIF or JPEG).

#### Endpoint

```
GET /api/v1/domain/current/logo
```

## Settings

The following API endpoints are for managing general settings.

### Read settings

Returns all settings.

#### Endpoint

```
GET /api/v1/setting/read.json
```

### Get setting value

Returns a specific setting value.

#### Parameters

| | | |
| --- | --- | --- |
| `name` | mandatory, TEXT | The name of the setting. |

#### Endpoint

```
GET /api/v1/setting/get
```

### Update settings

Updates the settings. You can update any number of settings, you don't have to include all of them. The parameters are not listed here (there are too many). Read the settings first to get a list of available settings, and then update the ones you would like to update. You can also define your own settings, but text-only.

#### Endpoint

```
POST /api/v1/setting/update.json
```
