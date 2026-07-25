# backups/ — workbook backups

**Before any programmatic edit to the Excel**, copy it here as `<name>-pre-<change>-YYYY-MM-DD.xlsx`. Then edit via **Excel COM** (PowerShell), never an openpyxl save — openpyxl strips cached formula values and silently destroys every computed score column. Gitignored.
