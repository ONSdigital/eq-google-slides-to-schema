#!/usr/bin/python3
import argparse
import json

from apiclient import discovery
from oauth2client import tools

from auth import auth_http
from extract import extract_content
from process import process_content, generate_id


def convert(flags):
    service = discovery.build('slides', 'v1', http=auth_http(flags))

    slides = get_slides(service, flags.presentation_id)

    groups = []
    blocks = []

    for i, slide in enumerate(slides):
        print('Processing Slide #{} (id={})...'.format(i + 1, slide.get('objectId')))
        content = extract_content(slide)
        if content:
            processed = process_content(i, content)
            block = generate_schema_block(processed)
            blocks.append(block)

            # Interstitial marks the end of a group
            if content.get('block_type') == 'Interstitial':
                group = generate_schema_group(i, blocks)
                groups.append(group)
                blocks = []

    if blocks:
        group = generate_schema_group(i+1, blocks)
        groups.append(group)

    schema = generate_schema(flags.survey_title, groups)
    with open(flags.out, 'w') as f:
        f.writelines(json.dumps(schema, indent=4, sort_keys=True))


def get_slides(service, presentation_id):
    presentation = service.presentations().get(
        presentationId=presentation_id).execute()
    slides = presentation.get('slides')
    print('The presentation contains {} slides:'.format(len(slides)))
    return slides


def generate_schema(survey_title, groups):
    schema = {
        'mime_type': 'application/json/ons/eq',
        'questionnaire_id': '',
        'schema_version': '0.0.1',
        'data_version': '0.0.2',
        'survey_id': generate_id(survey_title),
        'title': survey_title,
        'description': survey_title,
        'theme': 'default',
        'navigation': True,
        'groups': groups
    }

    return schema


def generate_schema_group(index, blocks):
    return {
        'id':  blocks[-1]['sections'][0]['id'] + '-group-' + str(index),
        'title': blocks[-1]['sections'][0]['title'],
        'blocks': blocks
    }


def generate_schema_block(content):
    block = {
        'type': content.get('block_type'),
        'id': content.get('block_id'),
        'sections': []
    }

    section = {
        'id': content.get('section_id'),
        'title': content.get('section_title'),
        'description': content.get('section_description'),
        'questions': []
    }

    if content.get('section_number'):
        section['number'] = content.get('section_number')

    block['sections'].append(section)

    if content.get('question_id'):
        question = {
            'id': content.get('question_id'),
            'title': content.get('question_title'),
            'description': content.get('question_description'),
            'type': 'General',
            'answers': content.get('answers')

        }

        if content.get('question_number'):
            question['number'] = content.get('question_number')

        if content.get('question_guidance'):
            question['guidance'] = content.get('question_guidance')

        block['sections'][0]['questions'].append(question)

    return block


if __name__ == '__main__':
    parser = argparse.ArgumentParser(parents=[tools.argparser])

    parser.add_argument('--presentation_id',
                        type=str,
                        required=True,
                        help='The id of the Google Slides presentation to convert')

    parser.add_argument('--out',
                        type=str,
                        default='slides.json',
                        help='The file path of where the JSON schema output should be stored')

    parser.add_argument('--survey_title',
                        type=str,
                        default='my survey',
                        help='The name of the survey')

    _flags = parser.parse_args()

    convert(_flags)
