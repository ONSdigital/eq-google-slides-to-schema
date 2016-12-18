# Google Slides to Schema

Utility for converting Google Slides to EQ Schema JSON files

## Setup
Based on python 3

If using virtualenvwrapper (if not, you should be), create a new virtual env for python3

```
mkvirtual --python=`which python3` <your env name>
```

Install dependencies using pip

```
pip install -r requirements.txt
```

Run the script with the id of the Google Slides presentation to convert

```
./convert.py --presentation_id=[...] --out=survey.json

```

This will generate a schema from the Google Slides. Run with no options
to see available arguments.
