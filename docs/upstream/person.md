Source: <https://app.cashctrl.com/static/help/en/api/index.html#/person>\
Fetched: 2026-10-23 (UTC)

## Person

The following API endpoints are for managing people / contacts.

### Read person

Returns a single person by ID.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |

#### Endpoint

```
GET /api/v1/person/read.json
```

### List people

Returns a list of people.

#### Parameters

<table>
<tr><th><code>categoryId</code></th><td>optional, NUMBER</td><td>The ID of the category to filter by.</td></tr>
<tr><th><code>dir</code></th><td>optional, TEXT</td><td>The direction of the sort order (ascending or descending). Defaults to 'ASC'. Possible values: ASC, DESC.</td></tr>
<tr><th><code>filter</code></th><td>optional, JSON</td><td>An array of filters to filter the list. All filters must match (AND).<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>comparison</code></th><td>optional, TEXT</td><td>Comparison type. Defaults to 'like'. Possible values: eq, like, gt, lt.</td></tr>
<tr><th><code>field</code></th><td>optional, TEXT</td><td>The name of the column to filter by.</td></tr>
<tr><th><code>value</code></th><td>optional, TEXT</td><td>Text to filter by, or a JSON array of multiple values (OR).</td></tr>
</table>
</td></tr>
<tr><th><code>limit</code></th><td>optional, NUMBER</td><td>The number of entries to retrieve. Defaults to 100.</td></tr>
<tr><th><code>onlyActive</code></th><td>optional, BOOLEAN</td><td>Flag to include only active people. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyCustomers</code></th><td>optional, BOOLEAN</td><td>Flag to include only customers. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyEmployees</code></th><td>optional, BOOLEAN</td><td>Flag to include only employees. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyFamilies</code></th><td>optional, BOOLEAN</td><td>Flag to include only families. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyInsurances</code></th><td>optional, BOOLEAN</td><td>Flag to include only insurances. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyNotes</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with notes. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyVendors</code></th><td>optional, BOOLEAN</td><td>Flag to include only vendors. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyWithImages</code></th><td>optional, BOOLEAN</td><td>Flag to include only people with images. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyWithoutCategory</code></th><td>optional, BOOLEAN</td><td>Flag to include only people without a category. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyWithoutRole</code></th><td>optional, BOOLEAN</td><td>Flag to include only people without a role. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>query</code></th><td>optional, TEXT</td><td>Fulltext search query.</td></tr>
<tr><th><code>sort</code></th><td>optional, TEXT</td><td>The column to sort the list by. Defaults to 'name'.</td></tr>
<tr><th><code>start</code></th><td>optional, NUMBER</td><td>The starting entry. Defaults to 0.</td></tr>
</table>

#### Endpoint

```
GET /api/v1/person/list.json
```

### Export to Excel

Returns an Excel file of the people list.

#### Parameters

<table>
<tr><th><code>categoryId</code></th><td>optional, NUMBER</td><td>The ID of the category to filter by.</td></tr>
<tr><th><code>columns</code></th><td>optional, CSV</td><td>The columns to include in the list, comma-separated. Check the list.json for available column names.</td></tr>
<tr><th><code>dir</code></th><td>optional, TEXT</td><td>The direction of the sort order (ascending or descending). Defaults to 'ASC'. Possible values: ASC, DESC.</td></tr>
<tr><th><code>filter</code></th><td>optional, JSON</td><td>An array of filters to filter the list. All filters must match (AND).<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>comparison</code></th><td>optional, TEXT</td><td>Comparison type. Defaults to 'like'. Possible values: eq, like, gt, lt.</td></tr>
<tr><th><code>field</code></th><td>optional, TEXT</td><td>The name of the column to filter by.</td></tr>
<tr><th><code>value</code></th><td>optional, TEXT</td><td>Text to filter by, or a JSON array of multiple values (OR).</td></tr>
</table>
</td></tr>
<tr><th><code>limit</code></th><td>optional, NUMBER</td><td>The number of entries to retrieve. Defaults to 100.</td></tr>
<tr><th><code>onlyActive</code></th><td>optional, BOOLEAN</td><td>Flag to include only active people. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyCustomers</code></th><td>optional, BOOLEAN</td><td>Flag to include only customers. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyEmployees</code></th><td>optional, BOOLEAN</td><td>Flag to include only employees. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyFamilies</code></th><td>optional, BOOLEAN</td><td>Flag to include only families. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyInsurances</code></th><td>optional, BOOLEAN</td><td>Flag to include only insurances. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyNotes</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with notes. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyVendors</code></th><td>optional, BOOLEAN</td><td>Flag to include only vendors. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyWithImages</code></th><td>optional, BOOLEAN</td><td>Flag to include only people with images. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyWithoutCategory</code></th><td>optional, BOOLEAN</td><td>Flag to include only people without a category. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyWithoutRole</code></th><td>optional, BOOLEAN</td><td>Flag to include only people without a role. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>query</code></th><td>optional, TEXT</td><td>Fulltext search query.</td></tr>
<tr><th><code>sort</code></th><td>optional, TEXT</td><td>The column to sort the list by. Defaults to 'name'.</td></tr>
<tr><th><code>start</code></th><td>optional, NUMBER</td><td>The starting entry. Defaults to 0.</td></tr>
</table>

#### Endpoint

```
GET /api/v1/person/list.xlsx
```

### Export to CSV

Returns a CSV file of the people list.

#### Parameters

<table>
<tr><th><code>categoryId</code></th><td>optional, NUMBER</td><td>The ID of the category to filter by.</td></tr>
<tr><th><code>columns</code></th><td>optional, CSV</td><td>The columns to include in the list, comma-separated. Check the list.json for available column names.</td></tr>
<tr><th><code>dir</code></th><td>optional, TEXT</td><td>The direction of the sort order (ascending or descending). Defaults to 'ASC'. Possible values: ASC, DESC.</td></tr>
<tr><th><code>filter</code></th><td>optional, JSON</td><td>An array of filters to filter the list. All filters must match (AND).<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>comparison</code></th><td>optional, TEXT</td><td>Comparison type. Defaults to 'like'. Possible values: eq, like, gt, lt.</td></tr>
<tr><th><code>field</code></th><td>optional, TEXT</td><td>The name of the column to filter by.</td></tr>
<tr><th><code>value</code></th><td>optional, TEXT</td><td>Text to filter by, or a JSON array of multiple values (OR).</td></tr>
</table>
</td></tr>
<tr><th><code>limit</code></th><td>optional, NUMBER</td><td>The number of entries to retrieve. Defaults to 100.</td></tr>
<tr><th><code>onlyActive</code></th><td>optional, BOOLEAN</td><td>Flag to include only active people. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyCustomers</code></th><td>optional, BOOLEAN</td><td>Flag to include only customers. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyEmployees</code></th><td>optional, BOOLEAN</td><td>Flag to include only employees. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyFamilies</code></th><td>optional, BOOLEAN</td><td>Flag to include only families. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyInsurances</code></th><td>optional, BOOLEAN</td><td>Flag to include only insurances. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyNotes</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with notes. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyVendors</code></th><td>optional, BOOLEAN</td><td>Flag to include only vendors. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyWithImages</code></th><td>optional, BOOLEAN</td><td>Flag to include only people with images. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyWithoutCategory</code></th><td>optional, BOOLEAN</td><td>Flag to include only people without a category. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyWithoutRole</code></th><td>optional, BOOLEAN</td><td>Flag to include only people without a role. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>query</code></th><td>optional, TEXT</td><td>Fulltext search query.</td></tr>
<tr><th><code>sort</code></th><td>optional, TEXT</td><td>The column to sort the list by. Defaults to 'name'.</td></tr>
<tr><th><code>start</code></th><td>optional, NUMBER</td><td>The starting entry. Defaults to 0.</td></tr>
</table>

#### Endpoint

```
GET /api/v1/person/list.csv
```

### Export to PDF

Returns a PDF file of the people list.

#### Parameters

<table>
<tr><th><code>categoryId</code></th><td>optional, NUMBER</td><td>The ID of the category to filter by.</td></tr>
<tr><th><code>columns</code></th><td>optional, CSV</td><td>The columns to include in the list, comma-separated. Check the list.json for available column names.</td></tr>
<tr><th><code>dir</code></th><td>optional, TEXT</td><td>The direction of the sort order (ascending or descending). Defaults to 'ASC'. Possible values: ASC, DESC.</td></tr>
<tr><th><code>filter</code></th><td>optional, JSON</td><td>An array of filters to filter the list. All filters must match (AND).<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>comparison</code></th><td>optional, TEXT</td><td>Comparison type. Defaults to 'like'. Possible values: eq, like, gt, lt.</td></tr>
<tr><th><code>field</code></th><td>optional, TEXT</td><td>The name of the column to filter by.</td></tr>
<tr><th><code>value</code></th><td>optional, TEXT</td><td>Text to filter by, or a JSON array of multiple values (OR).</td></tr>
</table>
</td></tr>
<tr><th><code>limit</code></th><td>optional, NUMBER</td><td>The number of entries to retrieve. Defaults to 100.</td></tr>
<tr><th><code>onlyActive</code></th><td>optional, BOOLEAN</td><td>Flag to include only active people. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyCustomers</code></th><td>optional, BOOLEAN</td><td>Flag to include only customers. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyEmployees</code></th><td>optional, BOOLEAN</td><td>Flag to include only employees. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyFamilies</code></th><td>optional, BOOLEAN</td><td>Flag to include only families. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyInsurances</code></th><td>optional, BOOLEAN</td><td>Flag to include only insurances. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyNotes</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with notes. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyVendors</code></th><td>optional, BOOLEAN</td><td>Flag to include only vendors. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyWithImages</code></th><td>optional, BOOLEAN</td><td>Flag to include only people with images. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyWithoutCategory</code></th><td>optional, BOOLEAN</td><td>Flag to include only people without a category. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyWithoutRole</code></th><td>optional, BOOLEAN</td><td>Flag to include only people without a role. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>query</code></th><td>optional, TEXT</td><td>Fulltext search query.</td></tr>
<tr><th><code>sort</code></th><td>optional, TEXT</td><td>The column to sort the list by. Defaults to 'name'.</td></tr>
<tr><th><code>start</code></th><td>optional, NUMBER</td><td>The starting entry. Defaults to 0.</td></tr>
</table>

#### Endpoint

```
GET /api/v1/person/list.pdf
```

### Export to vCard

Returns a vCard file containing a list of people.

#### Parameters

<table>
<tr><th><code>categoryId</code></th><td>optional, NUMBER</td><td>The ID of the category to filter by.</td></tr>
<tr><th><code>columns</code></th><td>optional, CSV</td><td>The columns to include in the list, comma-separated. Check the list.json for available column names.</td></tr>
<tr><th><code>dir</code></th><td>optional, TEXT</td><td>The direction of the sort order (ascending or descending). Defaults to 'ASC'. Possible values: ASC, DESC.</td></tr>
<tr><th><code>filter</code></th><td>optional, JSON</td><td>An array of filters to filter the list. All filters must match (AND).<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>comparison</code></th><td>optional, TEXT</td><td>Comparison type. Defaults to 'like'. Possible values: eq, like, gt, lt.</td></tr>
<tr><th><code>field</code></th><td>optional, TEXT</td><td>The name of the column to filter by.</td></tr>
<tr><th><code>value</code></th><td>optional, TEXT</td><td>Text to filter by, or a JSON array of multiple values (OR).</td></tr>
</table>
</td></tr>
<tr><th><code>limit</code></th><td>optional, NUMBER</td><td>The number of entries to retrieve. Defaults to 100.</td></tr>
<tr><th><code>onlyActive</code></th><td>optional, BOOLEAN</td><td>Flag to include only active people. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyCustomers</code></th><td>optional, BOOLEAN</td><td>Flag to include only customers. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyEmployees</code></th><td>optional, BOOLEAN</td><td>Flag to include only employees. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyFamilies</code></th><td>optional, BOOLEAN</td><td>Flag to include only families. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyInsurances</code></th><td>optional, BOOLEAN</td><td>Flag to include only insurances. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyNotes</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with notes. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyVendors</code></th><td>optional, BOOLEAN</td><td>Flag to include only vendors. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyWithImages</code></th><td>optional, BOOLEAN</td><td>Flag to include only people with images. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyWithoutCategory</code></th><td>optional, BOOLEAN</td><td>Flag to include only people without a category. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyWithoutRole</code></th><td>optional, BOOLEAN</td><td>Flag to include only people without a role. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>query</code></th><td>optional, TEXT</td><td>Fulltext search query.</td></tr>
<tr><th><code>sort</code></th><td>optional, TEXT</td><td>The column to sort the list by. Defaults to 'name'.</td></tr>
<tr><th><code>start</code></th><td>optional, NUMBER</td><td>The starting entry. Defaults to 0.</td></tr>
</table>

#### Endpoint

```
GET /api/v1/person/list.vcf
```

### Create person

Creates a new person. Returns either a success or multiple error messages (for each issue).

#### Parameters

<table>
<tr><th><code>company</code></th><td>mandatory, TEXT, MAX:100</td><td>The name of the organization / company. Either <code>firstName</code>, <code>lastName</code> or <code>company</code> must be set.</td></tr>
<tr><th><code>firstName</code></th><td>mandatory, TEXT, MAX:50</td><td>The person's first (given) name. Either <code>firstName</code>, <code>lastName</code> or <code>company</code> must be set.</td></tr>
<tr><th><code>lastName</code></th><td>mandatory, TEXT, MAX:50</td><td>The person's last (family) name. Either <code>firstName</code>, <code>lastName</code> or <code>company</code> must be set.</td></tr>
<tr><th><code>addresses</code></th><td>optional, TEXT</td><td>A list of addresses (street, house number, zip, city, country).<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>type</code></th><td>mandatory, TEXT</td><td>The type of address. Main address, invoice address, etc. Possible values: MAIN, INVOICE, DELIVERY, SALARY, HISTORICAL, OTHER.</td></tr>
<tr><th><code>address</code></th><td>optional, TEXT</td><td>The address (street, house number, additional info). Can contain multiple lines.</td></tr>
<tr><th><code>canton</code></th><td>optional, TEXT</td><td>The canton of the address (Switzerland only). Possible values: AG, AI, AR, BE, BL, BS, FR, GE, GL, GR, JU, LU, NE, NW, OW, SG, SH, SO, SZ, TG, TI, UR, VD, VS, ZG, ZH.</td></tr>
<tr><th><code>city</code></th><td>optional, TEXT</td><td>The town / city of the address.</td></tr>
<tr><th><code>company</code></th><td>optional, TEXT</td><td>Company name of the recipient.</td></tr>
<tr><th><code>country</code></th><td>optional, TEXT</td><td>The country of the address. Possible values: AFG, ALA, ALB, DZA, ASM, AND, AGO, AIA, ATG, ARG, ARM, ABW, AUS, AUT, AZE, BHS, BHR, BGD, BRB, BLR, BEL, BLZ, BEN, BMU, BTN, BOL, BES, BIH, BWA, BVT, BRA, IOT, BRN, BGR, BFA, BDI, KHM, CMR, CAN, CPV, CYM, CAF, TCD, CHL, CHN, CXR, CCK, COL, COM, COG, COK, CRI, CIV, HRV, CUB, CUW, CYP, CZE, DNK, DJI, DOM, DMA, ECU, EGY, SLV, GNQ, ERI, EST, ETH, FLK, FRO, FJI, FIN, FRA, GUF, GUY, PYF, GAB, GMB, GEO, DEU, GHA, GIB, GRC, GRL, GRD, GLP, GUM, GTM, GGY, GNB, GIN, HTI, HMD, VAT, HND, HKG, HUN, IND, IDN, IRN, IRQ, IRL, IMN, ISR, ITA, JAM, JPN, JEY, JOR, KAZ, KEN, KIR, PRK, KOR, KWT, KGZ, LAO, LVA, LBN, LSO, LBR, LBY, LIE, LTU, LUX, MAC, MKD, MDG, MWI, MYS, MDV, SOM, MLI, MLT, MHL, MTQ, MRT, MUS, MYT, MEX, FSM, MDA, MCO, MNG, MNE, MSR, MAR, MOZ, MMR, NAM, NRU, NPL, NLD, NCL, NZL, NIC, NGA, NER, NIU, NFK, MNP, NOR, OMN, PAK, PLW, PSE, PAN, PNG, PRY, PER, PHL, PCN, POL, PRT, PRI, QAT, REU, ROU, RUS, RWA, BLM, SHN, KNA, LCA, MAF, SPM, VCT, WSM, SMR, STP, SAU, SEN, SRB, SYC, SLE, SGP, SXM, SVK, SVN, SLB, ZAF, SGS, SSD, ESP, LKA, SDN, SUR, SJM, SWZ, SWE, CHE, SYR, TWN, TJK, TZA, THA, TLS, TGO, TKL, TON, TTO, TUN, TUR, TKM, TCA, TUV, UGA, UKR, ARE, GBR, USA, URY, UZB, VUT, VEN, VNM, VIR, VGB, WLF, YEM, ZMB, ZWE, ISL.</td></tr>
<tr><th><code>firstName</code></th><td>optional, TEXT</td><td>First name of the recipient.</td></tr>
<tr><th><code>isHideCompany</code></th><td>optional, BOOLEAN</td><td>Do not display the company name in the document address window. Possible values: true, false.</td></tr>
<tr><th><code>isHideName</code></th><td>optional, BOOLEAN</td><td>Do not display the title, first name and last name in the document address window. Possible values: true, false.</td></tr>
<tr><th><code>lastName</code></th><td>optional, TEXT</td><td>Last name of the recipient.</td></tr>
<tr><th><code>zip</code></th><td>optional, TEXT</td><td>The postal code of the address.</td></tr>
</table>
</td></tr>
<tr><th><code>altName</code></th><td>optional, TEXT, MAX:100</td><td>An alternative name for this person (for organizational chart).<br>This can contain localized text. To add values in multiple languages, use the XML format like this: <code>&lt;values&gt;&lt;de&gt;German text&lt;/de&gt;&lt;en&gt;English text&lt;/en&gt;&lt;/values&gt;</code></td></tr>
<tr><th><code>attachments</code></th><td>optional, JSON</td><td>List of files to attach.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>fileId</code></th><td>optional, NUMBER</td><td>ID of the file to attach. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/file">File</a>.</td></tr>
</table>
</td></tr>
<tr><th><code>bankAccounts</code></th><td>optional, TEXT</td><td>A list of bank accounts (IBAN, BIC).<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>iban</code></th><td>mandatory, TEXT, MAX:32</td><td>The IBAN (International Bank Account Number).</td></tr>
<tr><th><code>type</code></th><td>mandatory, TEXT</td><td>The type of bank account, i.e. what is the bank account used for? Possible values: DEFAULT, ORDER, SALARY, HISTORICAL, OTHER.</td></tr>
<tr><th><code>bic</code></th><td>optional, TEXT, MAX:11</td><td>The BIC (Business Identifier Code) of your bank.</td></tr>
<tr><th><code>notes</code></th><td>optional, TEXT, MAX:255</td><td>Some optional notes.</td></tr>
</table>
</td></tr>
<tr><th><code>bankData</code></th><td>optional, TEXT, MAX:255</td><td>Unstructured bank information, if IBAN/BIC not available. Otherwise use <code>bankAccounts</code>.</td></tr>
<tr><th><code>categoryId</code></th><td>optional, NUMBER</td><td>The ID of the category. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/person/category">Person category</a>.</td></tr>
<tr><th><code>certificateTemplateId</code></th><td>optional, NUMBER</td><td>The ID of the salary certificate template. <code>isEmployee</code> must be set.</td></tr>
<tr><th><code>certificateValues</code></th><td>optional, JSON</td><td>Values to print directly on the employee's salary certificate. <code>isEmployee</code> must be true, otherwise this is ignored. This overrides any values set on the <a href="https://app.cashctrl.com/static/help/en/api/index.html#/salary/certificate/template">salary certificate template</a>. This is a map of code -&gt; value, for example: {"F": true, "2.3a": "Bonus"}</td></tr>
<tr><th><code>children</code></th><td>optional, TEXT</td><td>A list of children. <code>isEmployee</code> or <code>isFamily</code> must be set.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>name</code></th><td>mandatory, TEXT</td><td>Name of the child (first and last name).</td></tr>
<tr><th><code>dateBenefitBegin</code></th><td>optional, DATE</td><td>Child benefit start date (used for salary statements).<br>Format: YYYY-MM-DD. Example: <code>2020-01-15</code>.</td></tr>
<tr><th><code>dateBenefitEnd</code></th><td>optional, DATE</td><td>Child benefit end date (used for salary statements).<br>Format: YYYY-MM-DD. Example: <code>2020-01-15</code>.</td></tr>
<tr><th><code>dateBirth</code></th><td>optional, DATE</td><td>The child's date of birth.<br>Format: YYYY-MM-DD. Example: <code>2020-01-15</code>.</td></tr>
<tr><th><code>dateInEducation</code></th><td>optional, DATE</td><td>Date since child is in education (used for salary statements).<br>Format: YYYY-MM-DD. Example: <code>2020-01-15</code>.</td></tr>
<tr><th><code>notes</code></th><td>optional, TEXT, MAX:255</td><td>Some optional notes.</td></tr>
</table>
</td></tr>
<tr><th><code>color</code></th><td>optional, TEXT</td><td>The color to use for this person in the organizational chart. Leave empty for white. Possible values: BLUE, GREEN, RED, YELLOW, ORANGE, BLACK, GRAY, BROWN, VIOLET, PINK.</td></tr>
<tr><th><code>contacts</code></th><td>optional, TEXT</td><td>A list of contact information (e-mail, phone, url, etc.).<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>address</code></th><td>mandatory, TEXT</td><td>The actual contact information (e-mail address, phone number, etc.).</td></tr>
<tr><th><code>type</code></th><td>mandatory, TEXT</td><td>The type of contact information. Possible values: EMAIL_INVOICE, EMAIL_WORK, EMAIL_PRIVATE, PHONE_RECEPTION, PHONE_WORK, PHONE_PRIVATE, MOBILE_WORK, MOBILE_PRIVATE, FAX, WEBSITE, MESSENGER, OTHER.</td></tr>
<tr><th><code>notes</code></th><td>optional, TEXT, MAX:255</td><td>Some optional short notes.</td></tr>
</table>
</td></tr>
<tr><th><code>custom</code></th><td>optional, XML</td><td>Custom field values. They are stored as XML in this parameter. Example: <code>&lt;values&gt;&lt;customField1&gt;My value&lt;/customField1&gt;&lt;customField2&gt;["value 1","value 2"]&lt;/customField2&gt;&lt;/values&gt;</code>. Look up custom field variable names (e.g. "customField1") in the <a href="https://app.cashctrl.com/static/help/en/api/index.html#/customfield">Custom fields</a> API.</td></tr>
<tr><th><code>dateBirth</code></th><td>optional, DATE</td><td>The person's date of birth.<br>Format: YYYY-MM-DD. Example: <code>2020-01-15</code>.</td></tr>
<tr><th><code>department</code></th><td>optional, TEXT, MAX:100</td><td>The department of the person within the company.</td></tr>
<tr><th><code>discountPercentage</code></th><td>optional, NUMBER, MIN:0.0, MAX:100.0</td><td>Discount percentage for this person, which may be used for orders. This can also be set on the category for all people in that category.</td></tr>
<tr><th><code>industry</code></th><td>optional, TEXT, MAX:100</td><td>The industry of the company or the trade/vocation of the person.</td></tr>
<tr><th><code>insuranceContracts</code></th><td>optional, TEXT</td><td>A list of insurance contracts, if <code>isInsurance</code> is set.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>typeId</code></th><td>mandatory, NUMBER</td><td>ID of the insurance type (e.g. AHV, BVG, etc.).</td></tr>
<tr><th><code>contractNr</code></th><td>optional, TEXT</td><td>Number of the contract with the insurance company.</td></tr>
<tr><th><code>subNr</code></th><td>optional, TEXT</td><td>Optional sub-contract number, if sub-contracts exist.</td></tr>
</table>
</td></tr>
<tr><th><code>insuranceMemberNr</code></th><td>optional, TEXT, MAX:32</td><td>Member number (for insurance). <code>isInsurance</code> must be set.</td></tr>
<tr><th><code>insuranceNr</code></th><td>optional, TEXT, MAX:32</td><td>Insurance number. <code>isInsurance</code> must be set.</td></tr>
<tr><th><code>isAutoFillResponsiblePerson</code></th><td>optional, BOOLEAN</td><td>Whether to autofill the responsible person field in order documents with this person if <code>userId</code> is set. Possible values: true, false.</td></tr>
<tr><th><code>isCustomer</code></th><td>optional, BOOLEAN</td><td>Is the person a customer? (role) Possible values: true, false.</td></tr>
<tr><th><code>isEmployee</code></th><td>optional, BOOLEAN</td><td>Is the person an employee? (role) Possible values: true, false.</td></tr>
<tr><th><code>isFamily</code></th><td>optional, BOOLEAN</td><td>Is the person a family? (role) Possible values: true, false.</td></tr>
<tr><th><code>isInactive</code></th><td>optional, BOOLEAN</td><td>Mark the person as inactive. The person will be greyed out and no longer suggested. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>isInsurance</code></th><td>optional, BOOLEAN</td><td>Is the person an insurance company? (role) Possible values: true, false.</td></tr>
<tr><th><code>isVendor</code></th><td>optional, BOOLEAN</td><td>Is the person a vendor? (role) Possible values: true, false.</td></tr>
<tr><th><code>language</code></th><td>optional, TEXT</td><td>The main language of the person. May be used for documents. Possible values: DE, EN, FR, IT.</td></tr>
<tr><th><code>locationId</code></th><td>optional, NUMBER</td><td>The ID of the location (workplace) of the employee. <code>isEmployee</code> must be set.</td></tr>
<tr><th><code>notes</code></th><td>optional, HTML</td><td>Some optional notes.<br>This can contain limited HTML for styling. Allowed tags: a, p, div, h1, h2, h3, h4, h5, h6, ul, ol, li, blockquote, b, i, s, u, o, sup, sub, ins, del, strong, strike, tt, code, big, small, br, span, em. Allowed inline CSS rules: background, background-color, color, font, font-size, font-weight, font-style, text-align, text-indent, text-decoration.</td></tr>
<tr><th><code>nr</code></th><td>optional, TEXT, MAX:50</td><td>The person number (e.g. customer no.).</td></tr>
<tr><th><code>position</code></th><td>optional, TEXT, MAX:100</td><td>The position (job title) of the person within the company.</td></tr>
<tr><th><code>sequenceNumberId</code></th><td>optional, NUMBER</td><td>The ID of the sequence number used to generate the person number (see <code>nr</code>). If this is empty, the sequence number will not update when <code>nr</code> is set. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/sequencenumber">Sequence number</a>.</td></tr>
<tr><th><code>servicePeriods</code></th><td>optional, TEXT</td><td>A list of service periods (entry and exit of the employee). <code>isEmployee</code> must be set.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>dateEntry</code></th><td>mandatory, DATE</td><td>The entry date.<br>Format: YYYY-MM-DD. Example: <code>2020-01-15</code>.</td></tr>
<tr><th><code>dateExit</code></th><td>optional, DATE</td><td>The exit date. Leave empty if this is the current period.<br>Format: YYYY-MM-DD. Example: <code>2020-01-15</code>.</td></tr>
<tr><th><code>notes</code></th><td>optional, TEXT, MAX:255</td><td>Some optional notes.</td></tr>
</table>
</td></tr>
<tr><th><code>ssn</code></th><td>optional, TEXT, MAX:32</td><td>Social security number of the employee. <code>isEmployee</code> must be set.</td></tr>
<tr><th><code>superiorId</code></th><td>optional, NUMBER</td><td>The superior of this person (for organizational chart).</td></tr>
<tr><th><code>titleId</code></th><td>optional, NUMBER</td><td>The person's title (e.g. 'Mr.', 'Mrs.', 'Dr.'). See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/person/title">Person title</a>.</td></tr>
<tr><th><code>userId</code></th><td>optional, NUMBER</td><td>The ID of the user linked to this person. This is a user that can login to CashCtrl. <code>isEmployee</code> must be set.</td></tr>
<tr><th><code>vatUid</code></th><td>optional, TEXT, MAX:32</td><td>The UID (VAT no.) of the company.</td></tr>
</table>

#### Endpoint

```
POST /api/v1/person/create.json
```

### Update person

Updates an existing person. Note that all parameters must be submitted, omitted parameters are treated as empty values. Returns either a success or multiple error messages (for each issue).

#### Parameters

<table>
<tr><th><code>company</code></th><td>mandatory, TEXT, MAX:100</td><td>The name of the organization / company. Either <code>firstName</code>, <code>lastName</code> or <code>company</code> must be set.</td></tr>
<tr><th><code>firstName</code></th><td>mandatory, TEXT, MAX:50</td><td>The person's first (given) name. Either <code>firstName</code>, <code>lastName</code> or <code>company</code> must be set.</td></tr>
<tr><th><code>id</code></th><td>mandatory, NUMBER</td><td>The ID of the person to update.</td></tr>
<tr><th><code>lastName</code></th><td>mandatory, TEXT, MAX:50</td><td>The person's last (family) name. Either <code>firstName</code>, <code>lastName</code> or <code>company</code> must be set.</td></tr>
<tr><th><code>addresses</code></th><td>optional, TEXT</td><td>A list of addresses (street, house number, zip, city, country).<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>type</code></th><td>mandatory, TEXT</td><td>The type of address. Main address, invoice address, etc. Possible values: MAIN, INVOICE, DELIVERY, SALARY, HISTORICAL, OTHER.</td></tr>
<tr><th><code>address</code></th><td>optional, TEXT</td><td>The address (street, house number, additional info). Can contain multiple lines.</td></tr>
<tr><th><code>canton</code></th><td>optional, TEXT</td><td>The canton of the address (Switzerland only). Possible values: AG, AI, AR, BE, BL, BS, FR, GE, GL, GR, JU, LU, NE, NW, OW, SG, SH, SO, SZ, TG, TI, UR, VD, VS, ZG, ZH.</td></tr>
<tr><th><code>city</code></th><td>optional, TEXT</td><td>The town / city of the address.</td></tr>
<tr><th><code>company</code></th><td>optional, TEXT</td><td>Company name of the recipient.</td></tr>
<tr><th><code>country</code></th><td>optional, TEXT</td><td>The country of the address. Possible values: AFG, ALA, ALB, DZA, ASM, AND, AGO, AIA, ATG, ARG, ARM, ABW, AUS, AUT, AZE, BHS, BHR, BGD, BRB, BLR, BEL, BLZ, BEN, BMU, BTN, BOL, BES, BIH, BWA, BVT, BRA, IOT, BRN, BGR, BFA, BDI, KHM, CMR, CAN, CPV, CYM, CAF, TCD, CHL, CHN, CXR, CCK, COL, COM, COG, COK, CRI, CIV, HRV, CUB, CUW, CYP, CZE, DNK, DJI, DOM, DMA, ECU, EGY, SLV, GNQ, ERI, EST, ETH, FLK, FRO, FJI, FIN, FRA, GUF, GUY, PYF, GAB, GMB, GEO, DEU, GHA, GIB, GRC, GRL, GRD, GLP, GUM, GTM, GGY, GNB, GIN, HTI, HMD, VAT, HND, HKG, HUN, IND, IDN, IRN, IRQ, IRL, IMN, ISR, ITA, JAM, JPN, JEY, JOR, KAZ, KEN, KIR, PRK, KOR, KWT, KGZ, LAO, LVA, LBN, LSO, LBR, LBY, LIE, LTU, LUX, MAC, MKD, MDG, MWI, MYS, MDV, SOM, MLI, MLT, MHL, MTQ, MRT, MUS, MYT, MEX, FSM, MDA, MCO, MNG, MNE, MSR, MAR, MOZ, MMR, NAM, NRU, NPL, NLD, NCL, NZL, NIC, NGA, NER, NIU, NFK, MNP, NOR, OMN, PAK, PLW, PSE, PAN, PNG, PRY, PER, PHL, PCN, POL, PRT, PRI, QAT, REU, ROU, RUS, RWA, BLM, SHN, KNA, LCA, MAF, SPM, VCT, WSM, SMR, STP, SAU, SEN, SRB, SYC, SLE, SGP, SXM, SVK, SVN, SLB, ZAF, SGS, SSD, ESP, LKA, SDN, SUR, SJM, SWZ, SWE, CHE, SYR, TWN, TJK, TZA, THA, TLS, TGO, TKL, TON, TTO, TUN, TUR, TKM, TCA, TUV, UGA, UKR, ARE, GBR, USA, URY, UZB, VUT, VEN, VNM, VIR, VGB, WLF, YEM, ZMB, ZWE, ISL.</td></tr>
<tr><th><code>firstName</code></th><td>optional, TEXT</td><td>First name of the recipient.</td></tr>
<tr><th><code>isHideCompany</code></th><td>optional, BOOLEAN</td><td>Do not display the company name in the document address window. Possible values: true, false.</td></tr>
<tr><th><code>isHideName</code></th><td>optional, BOOLEAN</td><td>Do not display the title, first name and last name in the document address window. Possible values: true, false.</td></tr>
<tr><th><code>lastName</code></th><td>optional, TEXT</td><td>Last name of the recipient.</td></tr>
<tr><th><code>zip</code></th><td>optional, TEXT</td><td>The postal code of the address.</td></tr>
</table>
</td></tr>
<tr><th><code>altName</code></th><td>optional, TEXT, MAX:100</td><td>An alternative name for this person (for organizational chart).<br>This can contain localized text. To add values in multiple languages, use the XML format like this: <code>&lt;values&gt;&lt;de&gt;German text&lt;/de&gt;&lt;en&gt;English text&lt;/en&gt;&lt;/values&gt;</code></td></tr>
<tr><th><code>attachments</code></th><td>optional, JSON</td><td>List of files to attach.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>fileId</code></th><td>optional, NUMBER</td><td>ID of the file to attach. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/file">File</a>.</td></tr>
</table>
</td></tr>
<tr><th><code>bankAccounts</code></th><td>optional, TEXT</td><td>A list of bank accounts (IBAN, BIC).<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>iban</code></th><td>mandatory, TEXT, MAX:32</td><td>The IBAN (International Bank Account Number).</td></tr>
<tr><th><code>type</code></th><td>mandatory, TEXT</td><td>The type of bank account, i.e. what is the bank account used for? Possible values: DEFAULT, ORDER, SALARY, HISTORICAL, OTHER.</td></tr>
<tr><th><code>bic</code></th><td>optional, TEXT, MAX:11</td><td>The BIC (Business Identifier Code) of your bank.</td></tr>
<tr><th><code>notes</code></th><td>optional, TEXT, MAX:255</td><td>Some optional notes.</td></tr>
</table>
</td></tr>
<tr><th><code>bankData</code></th><td>optional, TEXT, MAX:255</td><td>Unstructured bank information, if IBAN/BIC not available. Otherwise use <code>bankAccounts</code>.</td></tr>
<tr><th><code>categoryId</code></th><td>optional, NUMBER</td><td>The ID of the category. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/person/category">Person category</a>.</td></tr>
<tr><th><code>certificateTemplateId</code></th><td>optional, NUMBER</td><td>The ID of the salary certificate template. <code>isEmployee</code> must be set.</td></tr>
<tr><th><code>certificateValues</code></th><td>optional, JSON</td><td>Values to print directly on the employee's salary certificate. <code>isEmployee</code> must be true, otherwise this is ignored. This overrides any values set on the <a href="https://app.cashctrl.com/static/help/en/api/index.html#/salary/certificate/template">salary certificate template</a>. This is a map of code -&gt; value, for example: {"F": true, "2.3a": "Bonus"}</td></tr>
<tr><th><code>children</code></th><td>optional, TEXT</td><td>A list of children. <code>isEmployee</code> or <code>isFamily</code> must be set.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>name</code></th><td>mandatory, TEXT</td><td>Name of the child (first and last name).</td></tr>
<tr><th><code>dateBenefitBegin</code></th><td>optional, DATE</td><td>Child benefit start date (used for salary statements).<br>Format: YYYY-MM-DD. Example: <code>2020-01-15</code>.</td></tr>
<tr><th><code>dateBenefitEnd</code></th><td>optional, DATE</td><td>Child benefit end date (used for salary statements).<br>Format: YYYY-MM-DD. Example: <code>2020-01-15</code>.</td></tr>
<tr><th><code>dateBirth</code></th><td>optional, DATE</td><td>The child's date of birth.<br>Format: YYYY-MM-DD. Example: <code>2020-01-15</code>.</td></tr>
<tr><th><code>dateInEducation</code></th><td>optional, DATE</td><td>Date since child is in education (used for salary statements).<br>Format: YYYY-MM-DD. Example: <code>2020-01-15</code>.</td></tr>
<tr><th><code>notes</code></th><td>optional, TEXT, MAX:255</td><td>Some optional notes.</td></tr>
</table>
</td></tr>
<tr><th><code>color</code></th><td>optional, TEXT</td><td>The color to use for this person in the organizational chart. Leave empty for white. Possible values: BLUE, GREEN, RED, YELLOW, ORANGE, BLACK, GRAY, BROWN, VIOLET, PINK.</td></tr>
<tr><th><code>contacts</code></th><td>optional, TEXT</td><td>A list of contact information (e-mail, phone, url, etc.).<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>address</code></th><td>mandatory, TEXT</td><td>The actual contact information (e-mail address, phone number, etc.).</td></tr>
<tr><th><code>type</code></th><td>mandatory, TEXT</td><td>The type of contact information. Possible values: EMAIL_INVOICE, EMAIL_WORK, EMAIL_PRIVATE, PHONE_RECEPTION, PHONE_WORK, PHONE_PRIVATE, MOBILE_WORK, MOBILE_PRIVATE, FAX, WEBSITE, MESSENGER, OTHER.</td></tr>
<tr><th><code>notes</code></th><td>optional, TEXT, MAX:255</td><td>Some optional short notes.</td></tr>
</table>
</td></tr>
<tr><th><code>custom</code></th><td>optional, XML</td><td>Custom field values. They are stored as XML in this parameter. Example: <code>&lt;values&gt;&lt;customField1&gt;My value&lt;/customField1&gt;&lt;customField2&gt;["value 1","value 2"]&lt;/customField2&gt;&lt;/values&gt;</code>. Look up custom field variable names (e.g. "customField1") in the <a href="https://app.cashctrl.com/static/help/en/api/index.html#/customfield">Custom fields</a> API.</td></tr>
<tr><th><code>dateBirth</code></th><td>optional, DATE</td><td>The person's date of birth.<br>Format: YYYY-MM-DD. Example: <code>2020-01-15</code>.</td></tr>
<tr><th><code>department</code></th><td>optional, TEXT, MAX:100</td><td>The department of the person within the company.</td></tr>
<tr><th><code>discountPercentage</code></th><td>optional, NUMBER, MIN:0.0, MAX:100.0</td><td>Discount percentage for this person, which may be used for orders. This can also be set on the category for all people in that category.</td></tr>
<tr><th><code>industry</code></th><td>optional, TEXT, MAX:100</td><td>The industry of the company or the trade/vocation of the person.</td></tr>
<tr><th><code>insuranceContracts</code></th><td>optional, TEXT</td><td>A list of insurance contracts, if <code>isInsurance</code> is set.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>typeId</code></th><td>mandatory, NUMBER</td><td>ID of the insurance type (e.g. AHV, BVG, etc.).</td></tr>
<tr><th><code>contractNr</code></th><td>optional, TEXT</td><td>Number of the contract with the insurance company.</td></tr>
<tr><th><code>subNr</code></th><td>optional, TEXT</td><td>Optional sub-contract number, if sub-contracts exist.</td></tr>
</table>
</td></tr>
<tr><th><code>insuranceMemberNr</code></th><td>optional, TEXT, MAX:32</td><td>Member number (for insurance). <code>isInsurance</code> must be set.</td></tr>
<tr><th><code>insuranceNr</code></th><td>optional, TEXT, MAX:32</td><td>Insurance number. <code>isInsurance</code> must be set.</td></tr>
<tr><th><code>isAutoFillResponsiblePerson</code></th><td>optional, BOOLEAN</td><td>Whether to autofill the responsible person field in order documents with this person if <code>userId</code> is set. Possible values: true, false.</td></tr>
<tr><th><code>isCustomer</code></th><td>optional, BOOLEAN</td><td>Is the person a customer? (role) Possible values: true, false.</td></tr>
<tr><th><code>isEmployee</code></th><td>optional, BOOLEAN</td><td>Is the person an employee? (role) Possible values: true, false.</td></tr>
<tr><th><code>isFamily</code></th><td>optional, BOOLEAN</td><td>Is the person a family? (role) Possible values: true, false.</td></tr>
<tr><th><code>isInactive</code></th><td>optional, BOOLEAN</td><td>Mark the person as inactive. The person will be greyed out and no longer suggested. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>isInsurance</code></th><td>optional, BOOLEAN</td><td>Is the person an insurance company? (role) Possible values: true, false.</td></tr>
<tr><th><code>isVendor</code></th><td>optional, BOOLEAN</td><td>Is the person a vendor? (role) Possible values: true, false.</td></tr>
<tr><th><code>language</code></th><td>optional, TEXT</td><td>The main language of the person. May be used for documents. Possible values: DE, EN, FR, IT.</td></tr>
<tr><th><code>locationId</code></th><td>optional, NUMBER</td><td>The ID of the location (workplace) of the employee. <code>isEmployee</code> must be set.</td></tr>
<tr><th><code>notes</code></th><td>optional, HTML</td><td>Some optional notes.<br>This can contain limited HTML for styling. Allowed tags: a, p, div, h1, h2, h3, h4, h5, h6, ul, ol, li, blockquote, b, i, s, u, o, sup, sub, ins, del, strong, strike, tt, code, big, small, br, span, em. Allowed inline CSS rules: background, background-color, color, font, font-size, font-weight, font-style, text-align, text-indent, text-decoration.</td></tr>
<tr><th><code>nr</code></th><td>optional, TEXT, MAX:50</td><td>The person number (e.g. customer no.).</td></tr>
<tr><th><code>position</code></th><td>optional, TEXT, MAX:100</td><td>The position (job title) of the person within the company.</td></tr>
<tr><th><code>sequenceNumberId</code></th><td>optional, NUMBER</td><td>The ID of the sequence number used to generate the person number (see <code>nr</code>). If this is empty, the sequence number will not update when <code>nr</code> is set. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/sequencenumber">Sequence number</a>.</td></tr>
<tr><th><code>servicePeriods</code></th><td>optional, TEXT</td><td>A list of service periods (entry and exit of the employee). <code>isEmployee</code> must be set.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>dateEntry</code></th><td>mandatory, DATE</td><td>The entry date.<br>Format: YYYY-MM-DD. Example: <code>2020-01-15</code>.</td></tr>
<tr><th><code>dateExit</code></th><td>optional, DATE</td><td>The exit date. Leave empty if this is the current period.<br>Format: YYYY-MM-DD. Example: <code>2020-01-15</code>.</td></tr>
<tr><th><code>notes</code></th><td>optional, TEXT, MAX:255</td><td>Some optional notes.</td></tr>
</table>
</td></tr>
<tr><th><code>ssn</code></th><td>optional, TEXT, MAX:32</td><td>Social security number of the employee. <code>isEmployee</code> must be set.</td></tr>
<tr><th><code>superiorId</code></th><td>optional, NUMBER</td><td>The superior of this person (for organizational chart).</td></tr>
<tr><th><code>titleId</code></th><td>optional, NUMBER</td><td>The person's title (e.g. 'Mr.', 'Mrs.', 'Dr.'). See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/person/title">Person title</a>.</td></tr>
<tr><th><code>userId</code></th><td>optional, NUMBER</td><td>The ID of the user linked to this person. This is a user that can login to CashCtrl. <code>isEmployee</code> must be set.</td></tr>
<tr><th><code>vatUid</code></th><td>optional, TEXT, MAX:32</td><td>The UID (VAT no.) of the company.</td></tr>
</table>

#### Endpoint

```
POST /api/v1/person/update.json
```

### Delete people

Deletes one or multiple people. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the selected entries, comma-separated. |

#### Endpoint

```
POST /api/v1/person/delete.json
```

### Categorize people

Assigns one or multiple people to the desired category. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the entries to categorize, comma-separated. |
| `target` | mandatory, NUMBER | The ID of the target category. |

#### Endpoint

```
POST /api/v1/person/categorize.json
```

### Update attachments

Updates the file attachments of a person. Use the [File API](https://app.cashctrl.com/static/help/en/api/index.html#/file) to upload a file and then use the file ID here. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |
| `fileIds` | optional, CSV | A list of file IDs, comma-separated. Leave empty to remove all attachments. Use the [File API](https://app.cashctrl.com/static/help/en/api/index.html#/file) to upload a file and then use the file ID here. |

#### Endpoint

```
POST /api/v1/person/update_attachments.json
```

## Category

The following API endpoints are for managing person categories (e.g. 'Customers', 'Vendors', 'Employees').

### Read category

Returns a single category by ID.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |

#### Endpoint

```
GET /api/v1/person/category/read.json
```

### List categories

Returns a list of all categories.

#### Endpoint

```
GET /api/v1/person/category/list.json
```

### Get tree of categories

Returns a tree of all categories or the tree below a parent category.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | optional, NUMBER | Optional ID of the parent category (omit to get all categories). |

#### Endpoint

```
GET /api/v1/person/category/tree.json
```

### Create category

Creates a new category. Returns either a success or multiple error messages (for each issue).

#### Parameters

| | | |
| --- | --- | --- |
| `name` | mandatory, TEXT, MAX:50 | The name of the category.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: `<values><de>German text</de><en>English text</en></values>` |
| `discountPercentage` | optional, NUMBER, MIN:0.0, MAX:100.0 | Discount percentage for people in this category, which may be used for orders. |
| `parentId` | optional, NUMBER | The ID of the parent category. |
| `sequenceNrId` | optional, NUMBER | The ID of the sequence number used for people in this category. If empty, the sequence number of the parent category is inherited. |

#### Endpoint

```
POST /api/v1/person/category/create.json
```

### Update category

Updates an existing category. Note that all parameters must be submitted, omitted parameters are treated as empty values. Returns either a success or multiple error messages (for each issue).

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the category to update. |
| `name` | mandatory, TEXT, MAX:50 | The name of the category.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: `<values><de>German text</de><en>English text</en></values>` |
| `discountPercentage` | optional, NUMBER, MIN:0.0, MAX:100.0 | Discount percentage for people in this category, which may be used for orders. |
| `parentId` | optional, NUMBER | The ID of the parent category. |
| `sequenceNrId` | optional, NUMBER | The ID of the sequence number used for people in this category. If empty, the sequence number of the parent category is inherited. |

#### Endpoint

```
POST /api/v1/person/category/update.json
```

### Delete categories

Deletes one or multiple existing categories. Note that you can only delete empty categories. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the selected entries, comma-separated. |

#### Endpoint

```
POST /api/v1/person/category/delete.json
```

## Import

The following API endpoints are for importing people from a file, either a vCard, Excel or CSV file.

### Create import

Creates a new import session. Returns either a success or multiple error messages (for each issue).

#### Parameters

| | | |
| --- | --- | --- |
| `fileId` | mandatory, NUMBER | File to import. Valid formats: vCard, Excel and CSV. Max. size: 5 MB. Use the [File API](https://app.cashctrl.com/static/help/en/api/index.html#/file) to upload a file and then use the file ID here. |
| `categoryId` | optional, NUMBER | Category for all new people, overriding imported categories. |

#### Endpoint

```
POST /api/v1/person/import/create.json
```

### Define mapping

Defines the mapping from Excel / CSV column header names to CashCtrl fields. This step is not needed for vCards. See [List mapping fields](https://app.cashctrl.com/static/help/en/api/index.html#/person/import/mapping_combo.json) endpoint for a list of field names. Returns either a success or multiple error messages (for each issue).

#### Parameters

<table>
<tr><th><code>id</code></th><td>mandatory, NUMBER</td><td>Import session ID from the <a href="https://app.cashctrl.com/static/help/en/api/index.html#/person/import/create.json">Create</a> endpoint.</td></tr>
<tr><th><code>mapping</code></th><td>mandatory, JSON</td><td>Mapping from columns (Excel/CSV) to fields in CashCtrl.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>from</code></th><td>mandatory, TEXT</td><td>Column header name in Excel/CSV.</td></tr>
<tr><th><code>to</code></th><td>mandatory, TEXT</td><td>Field name in CashCtrl. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/person/import/mapping_combo.json">List mapping fields</a> endpoint for a list of field names.</td></tr>
</table>
</td></tr>
</table>

#### Endpoint

```
POST /api/v1/person/import/mapping.json
```

### List mapping fields

Lists the fields available in CashCtrl for mapping. Used in the [Define mapping](https://app.cashctrl.com/static/help/en/api/index.html#/person/import/mapping.json) endpoint.

#### Endpoint

```
GET /api/v1/person/import/mapping_combo.json
```

### Preview import

Previews the imported people. Returns a list of people that will be imported. This step can be omitted.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | Import session ID from the [Create](https://app.cashctrl.com/static/help/en/api/index.html#/person/import/create.json) endpoint. |

#### Endpoint

```
GET /api/v1/person/import/preview.json
```

### Execute import

Executes the importing of people from the import session.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | Import session ID from the [Create](https://app.cashctrl.com/static/help/en/api/index.html#/person/import/create.json) endpoint. |
| `indexes` | optional, CSV | Index numbers of people to import, comma-separated. All other people are ignored. You can get the indexes from the JSON response of the [Preview](https://app.cashctrl.com/static/help/en/api/index.html#/person/import/preview) endpoint. Omit this parameter to import all people. |

#### Endpoint

```
POST /api/v1/person/import/execute.json
```

## Title

The following API endpoints are for managing titles (forms of addressing people). A title is for example 'Mr.', 'Mrs.' or 'Dr.' and also contains gender and letter salutation.

### Read title

Returns a single title by ID.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |

#### Endpoint

```
GET /api/v1/person/title/read.json
```

### List titles

Returns a list of all titles.

#### Endpoint

```
GET /api/v1/person/title/list.json
```

### Create title

Creates a new title. Returns either a success or multiple error messages (for each issue).

#### Parameters

| | | |
| --- | --- | --- |
| `name` | mandatory, TEXT, MAX:50 | The name of the title (i.e. the actual title).<br>This can contain localized text. To add values in multiple languages, use the XML format like this: `<values><de>German text</de><en>English text</en></values>` |
| `gender` | optional, TEXT | The person's biological gender (male or female). Possible values: MALE, FEMALE. |
| `sentence` | optional, TEXT, MAX:250 | The letter salutation (e.g. 'Dear Mr.', etc.). May be used in mail. |

#### Endpoint

```
POST /api/v1/person/title/create.json
```

### Update title

Updates an existing title. Note that all parameters must be submitted, omitted parameters are treated as empty values. Returns either a success or multiple error messages (for each issue).

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the title to update. |
| `name` | mandatory, TEXT, MAX:50 | The name of the title (i.e. the actual title).<br>This can contain localized text. To add values in multiple languages, use the XML format like this: `<values><de>German text</de><en>English text</en></values>` |
| `gender` | optional, TEXT | The person's biological gender (male or female). Possible values: MALE, FEMALE. |
| `sentence` | optional, TEXT, MAX:250 | The letter salutation (e.g. 'Dear Mr.', etc.). May be used in mail. |

#### Endpoint

```
POST /api/v1/person/title/update.json
```

### Delete titles

Deletes one or multiple titles. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the selected entries, comma-separated. |

#### Endpoint

```
POST /api/v1/person/title/delete.json
```
