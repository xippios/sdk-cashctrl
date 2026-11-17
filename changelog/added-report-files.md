- Reports download as PDF and Excel files, Python only like the other file tasks:
  `download_report` writes one report, such as the balance sheet, `download_report_collection`
  a collection of them as one document, and `download_annual_report` the annual report's
  PDF. A file that holds a payroll or people report is refused before its download, by the
  rule of `get_report_data` on the report tree read right then.
  (https://github.com/xippios/sdk-cashctrl/issues/45)
