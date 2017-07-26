#!/usr/bin/env python
import argparse
import os
import pathlib
import yaml

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
            block = generate_manifest_block(processed)
            create_yaml_block(flags, block)
            blocks.append(block['id'])

            # Interstitial marks the end of a group
            if content.get('block_type') == 'Interstitial':
                group = generate_manifest_group(len(groups), blocks)
                groups.append(group)
                blocks = []

    if blocks:
        group = generate_manifest_group(len(groups), blocks)
        groups.append(group)

    manifest = generate_manifest(flags.survey_title, groups)
    manifest_file = os.path.join(flags.manifest_out, flags.survey_title + '.yaml')
    with open(manifest_file, 'w') as f:
        yaml.dump(manifest, f, default_flow_style=False)


def create_yaml_block(flags, block):
    """
    Checks if a YAML block file already exists for the given block,
    if so, compares the content of the file with the given
    block and creates a new variant YAML block file if different.
    If there is no existing YAML file then a new one is created.
    :param flags: Parses user input to define block file names
    :param block: Generated manifest block
    :return: Returns Block Yaml files
    """
    block_file = os.path.join(flags.blocks_out, block['id'] + '.yaml')

    if os.path.isfile(block_file):
        with open(block_file, 'r+') as f:
            block_content = yaml.load(f)

        if block_content != block:

            block_file_variant = os.path.join(flags.blocks_out, block['id'] + '-' + flags.survey_variant + '.yaml')

            with open(block_file_variant, 'w') as f:
                yaml.dump(block, f, default_flow_style=False)

    else:
        with open(block_file, 'w') as f:
            yaml.dump(block, f, default_flow_style=False)


def get_slides(service, presentation_id):
    presentation = service.presentations().get(
        presentationId=presentation_id).execute()
    slides = presentation.get('slides')
    print('The presentation contains {} slides:'.format(len(slides)))
    return slides


def generate_manifest(survey_title, groups):
    manifest = {
        'legal_basis': "StatisticsOfTradeAct",
        'mime_type': 'application/json/ons/eq',
        'schema_filename': '',
        'schema_version': '0.0.1',
        'data_version': '0.0.2',
        'survey_id': generate_id(survey_title),
        'title': survey_title,
        'description': survey_title,
        'theme': 'default',
        'groups': groups
    }

    return manifest


def generate_manifest_group(index, blocks):
    return {
        'id': 'group-{}'.format(index),
        'title': '',
        'blocks': blocks
    }


def generate_manifest_block(content: object) -> object:
    block = {
        'type': content.get('block_type'),
        'id': content.get('block_id'),
        'title': content.get('block_title'),
        'questions': []
    }

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

    block['questions'].append(question)

    return block


if __name__ == '__main__':
    parser = argparse.ArgumentParser(parents=[tools.argparser])

    parser.add_argument('--presentation_id',
                        type=str,
                        required=True,
                        help='The id of the Google Slides presentation to convert, an example can be found in '
                             'the README')

    parser.add_argument('--manifest_out',
                        type=str,
                        default='Manifests',
                        help='The directory path of where the YAML manifest output should be stored')

    parser.add_argument('--blocks_out',
                        type=str,
                        default='Blocks',
                        help='The directory path of where the YAML block(s) output should be stored')

    parser.add_argument('--survey_title',
                        type=str,
                        default='manifest',
                        help='The name of the YAML manifest file created, e.g. 0102.rsi.manifest')

    parser.add_argument('--survey_variant',
                        type=str,
                        default='variant',
                        help='The form type, e.g. 0102')

    _flags = parser.parse_args()

    pathlib.Path(_flags.blocks_out).mkdir(parents=True, exist_ok=True)

    pathlib.Path(_flags.manifest_out).mkdir(parents=True, exist_ok=True)

    convert(_flags)






