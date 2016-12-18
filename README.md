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

## Google Slides API Access

Follow the instructions in the Quickstart guide here:
https://developers.google.com/slides/quickstart/python

Specifically the section "Step 1: Turn on the Google Slides API"

You will need to store the 'client_secret.json' in the same directory
as this project. **DO NOT PUSH THIS TO GITHUB**.

## Usage 
For help using:
```
./convert.py --help
```

Example with the id of a Google Slides presentation to convert and 
output file:
```
./convert.py --presentation_id=[...] --out=survey.json
```

You will need to authorise the project to access Google Slides with
a valid Google account that has access the presentations you want
to process. This is separate from the API access and is requested
at runtime.

