# Re:Dive Master Data Downloader

Guess the TruthVersion of プリコネR Taiwan server and download the database

## Outputs

* ``version.json`` - Contains current TruthVersion and hash
* ``redive_tw.db`` - The latest database
* ``redive_tw.db.br`` - Same as above, but compressed with Brotli
* ``prev.redive_tw.db`` - Previous version of the database
* ``diff/{TruthVersion}.sql`` - SQL diff report
