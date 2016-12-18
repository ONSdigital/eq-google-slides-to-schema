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

## Presentation Format
In order to extract content from the Slides into a schema some 
conventions need to be followed.

Primarily the system uses the font-size to differentiate between
elements on slides, such as a question title being 20pts and an answer
label being 14pts etc.

The font-size mappings are as follows:

Element | Font Size (pt)
------- | --------------
Interstitial Title | 30
Interstitial Description | 22
Section Title | 24
Section Description | 22
Question Title | 20
Question Description | 18
Question Guidance | 16
Answer Label | 14
Answer Description | 12
Answer Option | 13

Question Guidance is further processed based on the following:

Element | Formatting
------- | ----------
Guidance Heading | bold
Guidance Description | none
Guidance List Item | bullet-list

Any text that is not BLACK is ignored (for example so that notes can be
added to slides as blue-text without affecting the schema). Note that 
if text isn't appearing in the schema and looks BLACK in Google Slides
it may actually be a shade of grey, check the colour is set correctly.

Answer types are determined based on the existance of shapes on the 
slide as follows:

Type | Shape
---- | -----
Radio | Ellipse (Cirlce)    
Checkbox | Rectangle with RED outline
Currency | Rounded Rectangle
Comments | Rectangle with GREEN outline
Numeric | N/A - Assumed if none of the above shapes seen

Any slides with the NO_SMOKING shape on it will be ignored completely,
useful for non-questionnare slides, such as notes etc.

Questionnaire groups are generated for each interstitial encountered;
all questionnaire blocks since the last interstitial up to and include 
the next interstitial are included in the group. The section title
on the interstitial is used as the group title.

## Example Google Slide Presentation
Example template here: 

- https://docs.google.com/presentation/d/1NEYDvueIrHrvhlKjM788Z978v5Dyu_ejjv55bND8PZs/

The presentation_id is the value in the URL e.g.

- `1NEYDvueIrHrvhlKjM788Z978v5Dyu_ejjv55bND8PZs`