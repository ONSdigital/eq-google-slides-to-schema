import re


def process_content(index, extracted):

    elements = sorted(extracted.get('elements'), key=_get_transform_y)

    block_type = extracted.get('block_type')
    is_interstitial = _is_interstitial(elements)

    # Interstitial title is actually a section title
    section_title = _content_for_type_as_list(elements, 'section_title')
    if is_interstitial:
        section_title = _content_for_type_as_list(elements, 'interstitial_title')

    section = {
        'block_id': '',
        'block_type': 'interstitial' if is_interstitial else 'questionnaire',
        'section_id': '',
        'section_title': _process_title(section_title),
        'section_description': _process_description(_content_for_type_as_list(elements, 'section_description')),
        'section_number': _process_number(section_title)
    }

    question = {
        'question_id': _generate_id(section_title, 'question', index),
        'question_title': _process_title(_content_for_type_as_list(elements, 'question_title')),
        'question_description': _process_description(_content_for_type_as_list(elements, 'question_description')),
        'question_guidance':  _process_question_guidance(elements),
        'question_number': _process_number(_content_for_type_as_list(elements, 'question_title')),
        'answers': _process_answers(block_type, section_title, index, elements)
    }

    section.update(question)

    section['block_id'] = _generate_id(section_title, 'block', index)
    section['section_id'] = _generate_id(section_title, 'section', index)

    return section


def _process_answers(block_type, section_title, index, elements):
    """
    Loop through the elements (assumes they are ordered by y-transform) and generate answers.

    Uses the y-transform of the answer labels to work out how many answers there are (if the Y-Transform of the
    label is > than the last label it is a new answer)

    :param block_type: The type of block this is (e.g. Radio, Checkbox)
    :param section_title: The title of the section within this block
    :param index: The index of the section this answer is within
    :param elements: The y-transform ordered list of elements for this block
    :return: A list of answers (schema ready)
    """
    answers = []
    answer = {
        "id": _generate_id(section_title, 'answer', index, '-', 0),
        "label": "",
        "description": "",
        "type": block_type,
        "mandatory": False,
        "options": [],
    }

    last_label_paragraph_index = -1
    last_option_paragraph_index = -1

    for element in filter(lambda x: x['type'].startswith('answer_'), elements):

        if element.get('type') == 'answer_label':
            if last_label_paragraph_index is None:
                last_label_paragraph_index = element.get('paragraph_index')
                answer['label'] += element.get('content')

            elif element.get('paragraph_index') == last_label_paragraph_index:
                answer['label'] += element.get('content')

            else:
                # New label, start a new answer set
                if not _is_empty_answer(answer):
                    answers.append(answer)
                last_label_paragraph_index = element.get('paragraph_index')
                answer = {
                    "id": _generate_id(section_title, 'answer', index, '-', len(answers)),
                    "label": element.get('content'),
                    "description": '',
                    "type": block_type,
                    "mandatory": False,
                    "options": [],
                }

        elif element.get('type') == 'answer_option':
            if last_option_paragraph_index != element.get('paragraph_index'):
                last_option_paragraph_index = element.get('paragraph_index')
                answer['options'].extend(_process_option(element.get('content')))
            else:
                _append_option(answer['options'][-1], element.get('content'))

        elif element.get('type') == 'answer_prompt':
            answer['description'] += element.get('content')

        else:
            raise ValueError('unsupported element: {}'.format(element))

    # Catch the last answer if not empty
    if not _is_empty_answer(answer):
        answers.append(answer)

    return answers


def _is_empty_answer(answer):
    return not answer.get('label').strip() \
           and not answer.get('description').strip() \
           and not answer.get('options')


def _process_question_guidance(elements):
    """
    Loop through the guidance elements (assumes they are ordered by y-transform) and generate guidance JSON.

    :param elements: The list of elements for this block
    :return: A list of guidance (schema ready)
    """
    guidii = []
    guidance = {
        "title": "",
        "description": "",
        "list": []
    }

    last_list_paragraph_index = -1
    last_title_paragraph_index = -1

    for element in filter(lambda x: x['type'].startswith('question_guidance_'), elements):
        if element.get('type') == 'question_guidance_title':
            if element.get('paragraph_index') == last_title_paragraph_index:
                guidance['title'] += element.get('content')
            else:
                # This must be a new guidance section
                last_title_paragraph_index = element.get('paragraph_index')
                if not _is_guidance_empty(guidance):
                    guidii.append(guidance)
                guidance = {
                    "title": element.get('content'),
                    "description": "",
                    "list": []
                }

        elif element.get('type') == 'question_guidance_description':
            guidance['description'] += element.get('content')

        elif element.get('type') == 'question_guidance_list':
            if element.get('paragraph_index') == last_list_paragraph_index and guidance['list']:
                guidance['list'][-1] += element.get('content')
            else:
                guidance['list'].append(element.get('content'))
                last_list_paragraph_index = element.get('paragraph_index')

        else:
            raise ValueError('unsupported element: {}'.format(element))

    if not _is_guidance_empty(guidance):
        # Catch the last guidance if not empty
        guidii.append(guidance)

    return guidii


def _is_guidance_empty(guidance):
    return not guidance.get('title').strip() and not guidance.get('description').strip() and not guidance.get('list')


def _get_transform_y(element):
    """
    Extracts the translateY for an element from its transform.
    :return: an int representing the translateY value from the transform
    """
    return element.get('transform').get('translateY')


def _filter_by_type(elements, _type):
    """
    Returns an iterator that yields all elements with a type of _type
    :param elements:
    :param _type: the type of element (e.g. 'section_title')
    :return: An iterator
    """
    return filter(lambda x: x.get('type') == _type, elements)


def _content_for_type_as_list(elements, _type):
    """
    Returns the list of elements that had a 'type' of _type
    :param _type: The type of element (e.g. 'section_title')
    :return: A list
    """
    return [x.get('content') for x in _filter_by_type(elements, _type)]


def _is_interstitial(elements):
    for interstitial in _filter_by_type(elements, 'interstitial_title'):
        if len(interstitial.get('content')) > 0:
            return True

    return False


def _generate_id(*args):
    """
    Generate an id value from a list of arguments (lowercase with - separators)
    :param args: Arbitrary length list of arguments to form the id from
    :return: A str id value
    """
    _id = '-'.join([str(x) for x in args])
    _id = _id.lower()

    parts = re.sub('[^0-9a-zA-Z]+', '-', _id)
    return ''.join(parts)


def _clean_join(content):
    """
    Joins a list of values together and cleans (removes newlines and extraneous whitespace)
    :param content: A str or list of str to process
    :return: The joined/cleaned str
    """
    if not isinstance(content, str):
        content = ''.join(content) if content else ''
    return content.replace('\n', '')


def _process_title(content):
    title = _clean_join(content)
    return _extract_title_number(title).get('title')


def _process_label(content):
    return _clean_join(content)


def _process_number(content):
    title = _clean_join(content)
    return _extract_title_number(title).get('number')


def _process_description(content):
    """
    Joins a list of str together and creates basic HTML paragraphs around newlines.
    :param content: A list of str to process
    :return: the combined HTML str
    """
    content = ''.join(content) if content else ''
    html = ''

    if content:
        paragraphs = content.split('\n')
        for paragraph in [x for x in paragraphs if x]:
            html += '<p>' + paragraph + '</p>'

    return html


def _process_option(content):
    """
    Converts content into a radio/checkbox option schema output
    :return: A dict ready for use in the JSON Schema as a radio/check option
    """
    val = _clean_join(content)
    return [{
        "label": val,
        "value": val
    }]


def _append_option(option, content):
    """
    Appends to an existing option with more content
    """
    val = _clean_join(content)
    option["label"] += val
    option["value"] += val


def _extract_title_number(text):
    """
    Extracts the question/section number and title from a line of text
    Example format: '2.3 What is your name?'
    :param text: Text optionally containing a section/question number
    :return: A dict with the 'number' and 'title' extracted from the original 'text'
    """
    match = re.match('^([0-9.]*)?\s*(.*)', text)
    groups = match.groups()
    number = groups[0]
    title = groups[1]

    # Strip trailing dot .
    if number and number[-1] == '.':
        number = number[0:-1]

    return {'number': number, 'title': title}
