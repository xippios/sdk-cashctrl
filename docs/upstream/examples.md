Source: <https://app.cashctrl.com/static/help/en/api/index.html#examples>\
Fetched: 2026-10-23 (UTC)

## Examples

The following examples use cURL to perform various tasks via the API.

Note for all examples: Replace `myorg` with the sub-domain of the organization you're accessing. And replace `zjdqcZjsfSYyM4EPG19tHss6X5NIHf0b` with your API key. The colon after the key prevents curl from asking for a password.

#### Get journal book entries

Retrieves the journal book entries for the current fiscal period:

```
curl https://myorg.cashctrl.com/api/v1/journal/list.json -u zjdqcZjsfSYyM4EPG19tHss6X5NIHf0b:
```

#### Add a new location

Adds a location for your organization. This includes setting the logo from an uploaded file. To upload the file first, see [Upload one or multiple files](https://app.cashctrl.com/static/help/en/api/index.html#example-file) below.

```
curl https://myorg.cashctrl.com/api/v1/location/create.json -u zjdqcZjsfSYyM4EPG19tHss6X5NIHf0b: -X POST -F "name=Maria Muster Headquarters" -F "orgName=Maria Muster Inc." -F "logoFileId=201"
```

#### Import vCards

Imports a vCard (.vcf) file into the list of people. For this to work, you must first upload a file. See [Upload one or multiple files](https://app.cashctrl.com/static/help/en/api/index.html#example-file) below.

**Step 1: Create import session**

```
curl https://myorg.cashctrl.com/api/v1/person/import/create.json -u zjdqcZjsfSYyM4EPG19tHss6X5NIHf0b: -X POST -F "fileId=314"
```

**Step 2: Execute the import**

Use the insertId information from the response of the first step as the ID here.

```
curl https://myorg.cashctrl.com/api/v1/person/import/execute.json -u zjdqcZjsfSYyM4EPG19tHss6X5NIHf0b: -X POST -F "id=21"
```

#### Add a manual book entry

Creates a new book entry in the journal. You may need to adapt the account IDs (debitId/creditId) according to your chart of accounts:

```
curl https://myorg.cashctrl.com/api/v1/journal/create.json -u zjdqcZjsfSYyM4EPG19tHss6X5NIHf0b: -X POST -F "dateAdded=2020-07-06" -F "title=API generated book entry" -F "sequenceNumberId=6" -F "debitId=1" -F "creditId=15" -F "taxId=1" -F "amount=500"
```

#### Add a collective book entry

Creates a new collective book entry in the journal. The items are encoded as JSON, which has to be properly escaped:

```
curl https://myorg.cashctrl.com/api/v1/journal/create.json -u zjdqcZjsfSYyM4EPG19tHss6X5NIHf0b: -X POST -F "dateAdded=2020-07-06" -F "title=API generated collective entry" -F "sequenceNumberId=6" -F "items=[{\"accountId\":1,\"debit\":500},{\"accountId\":42,\"credit\":250},{\"accountId\":15,\"credit\":250}]"
```

#### Add an invoice

Creates a new sales invoice. The items are encoded as JSON, which has to be properly escaped. This example also creates a new person named "New customer" (use a person ID otherwise).

```
curl https://myorg.cashctrl.com/api/v1/order/create.json -u zjdqcZjsfSYyM4EPG19tHss6X5NIHf0b: -X POST -F "categoryId=4" -F "date=2020-07-06" -F "sequenceNumberId=1" -F "description=API generated invoice" -F "associateId=New customer" -F "accountId=4" -F "roundingId=1" -F "items=[{\"accountId\":15,\"taxId\":1,\"unitId\":2,\"articleNr\":\"S-0002\",\"quantity\":6,\"name\":\"Design\",\"unitPrice\":172.32},{\"accountId\":15,\"taxId\":1,\"unitId\":2,\"articleNr\":\"S-0001\",\"quantity\":15,\"name\":\"Web development\",\"unitPrice\":172.32}]"
```

#### Add person with custom fields

Creates a new person with additional custom fields. Custom fields are XML-encoded. Assuming two custom fields with identifier customField1 and customField2 have been created beforehand:

```
curl https://myorg.cashctrl.com/api/v1/person/create.json -u zjdqcZjsfSYyM4EPG19tHss6X5NIHf0b: -X POST -F "firstName=Stefan" -F "lastName=Meier" --form-string "custom=<values><customField1>Blue</customField1><customField2>Vanilla</customField2></values>"
```

#### Get the annual report PDF

Retrieves the annual report PDF in French:

```
curl https://myorg.cashctrl.com/api/v1/report/collection/download_annualreport.pdf?lang=fr -u zjdqcZjsfSYyM4EPG19tHss6X5NIHf0b:
```

#### Upload one or multiple files

There are three steps to uploading files: [Prepare](https://app.cashctrl.com/static/help/en/api/index.html#example-file-prepare) → [Put](https://app.cashctrl.com/static/help/en/api/index.html#example-file-put) → [Persist](https://app.cashctrl.com/static/help/en/api/index.html#example-file-persist). Let's say we upload two files: report.pdf and image.png.

**Step 1: Prepare**

We first inform CashCtrl of the file names and mime types of the files we are going to upload:

```
curl https://myorg.cashctrl.com/api/v1/file/prepare.json -u zjdqcZjsfSYyM4EPG19tHss6X5NIHf0b: -X POST -F "files=[{\"name\":\"report.pdf\",\"mimeType\":\"application/pdf\"},{\"name\":\"image.png\",\"mimeType\":\"image/png\"}}]"
```

This will return a list of file IDs and pre-authenticated write URLs where you can upload the files using the HTTP PUT method. Example response:

```
{
    "success": true,
    "data": [
        {
            "fileId": 24,
            "writeUrl": "https://objectstorage.eu-zurich-1.oraclecloud.com/p/pCmCfv9GwIxISZ9pGusMqiG9vG_TqAmU8QXgUhZ6C-W6j1CXYceSoqPQSQVXr0Fx/n/zry79ircxznv/b/dev/o/rihligXi/file/hh/au/report.pdf"
        },
        {
            "fileId": 25,
            "writeUrl": "https://objectstorage.eu-zurich-1.oraclecloud.com/p/1gi7PDkRphcQRe7bYE4WgM84DJ3uS-v-iN5ldGqgD2MJswZSTqfj1xE5T7F8PBtX/n/zry79ircxznv/b/dev/o/rihligXi/file/jc/zh/image.png"
        }
    ]
}
```

**Step 2: Put**

In the second step, we actually upload the files via HTTP PUT:

```
curl https://objectstorage.eu-zurich-1.oraclecloud.com/p/pCmCfv9GwIxISZ9pGusMqiG9vG_TqAmU8QXgUhZ6C-W6j1CXYceSoqPQSQVXr0Fx/n/zry79ircxznv/b/dev/o/rihligXi/file/hh/au/report.pdf --upload-file report.pdf

curl https://objectstorage.eu-zurich-1.oraclecloud.com/p/1gi7PDkRphcQRe7bYE4WgM84DJ3uS-v-iN5ldGqgD2MJswZSTqfj1xE5T7F8PBtX/n/zry79ircxznv/b/dev/o/rihligXi/file/jc/zh/image.png --upload-file image.png
```

The files have now been uploaded and are marked temporary. They will be deleted within 4 hours unless persisted with the final step. This final step depends on what you want to do. Note that any of these steps persists the temporary files.

**Step 3.a) Persist directly**

You just want to save the files and see them in the CashCtrl file manager:

```
curl https://myorg.cashctrl.com/api/v1/file/persist.json -u zjdqcZjsfSYyM4EPG19tHss6X5NIHf0b: -X POST -F "ids=24,25"
```

**Step 3.b) Persist with additional information**

You want to add a description, notes, custom fields, etc. to each file, instead of just persisting the files:

```
curl https://myorg.cashctrl.com/api/v1/file/create.json -u zjdqcZjsfSYyM4EPG19tHss6X5NIHf0b: -X POST -F "id=24" -F "name=report.pdf" -F "description=API generated report"

curl https://myorg.cashctrl.com/api/v1/file/create.json -u zjdqcZjsfSYyM4EPG19tHss6X5NIHf0b: -X POST -F "id=25" -F "name=image.png" "notes=Some API generated notes"
```

**Step 3.c) Attach to an entry**

You want to attach the files to a Person entry (`id` being the Person ID):

```
curl https://myorg.cashctrl.com/api/v1/person/update_attachments.json -u zjdqcZjsfSYyM4EPG19tHss6X5NIHf0b: -X POST -F "id=47" "fileIds=24,25"
```

**Step 3.d) Use the file as a logo, or for importing something**

You want to set the file as the logo of your organization or a location. See [Add new location](https://app.cashctrl.com/static/help/en/api/index.html#example-location) example above. You basically set a parameter named `logoFileId` (or similar) in the corresponding endpoint. Or you want to [Import a vCard](https://app.cashctrl.com/static/help/en/api/index.html#example-import-vcard) file for importing contacts.

#### Download a file

Downloads a file that you have previously uploaded (see previous example). Please be aware that the response may redirect to the actual file URL (a pre-authenticated cloud storage URL), so be sure to handle redirects. Using cURL, we can simply add the `-L` parameter.

```
curl https://myorg.cashctrl.com/api/v1/file/get?id=24 -u zjdqcZjsfSYyM4EPG19tHss6X5NIHf0b: -L
```
