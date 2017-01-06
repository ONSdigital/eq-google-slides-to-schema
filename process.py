import re

from utils import get_dict_nested_value


def process_content(index, extracted):

    elements = sorted(extracted.get('elements'), key=_get_transform_y)

    is_interstitial = _is_interstitial(elements)

    # Interstitial title is actually a section title
    section_title_name = 'section_title'
    if is_interstitial:
        section_title_name = 'interstitial_title'

    section = {
        'block_id': '',
        'block_type': 'interstitial' if is_interstitial else 'questionnaire',
        'section_id': '',
        'section_title': _process_title(elements, section_title_name),
        'section_description': _process_description(elements, 'section_description'),
        'section_number': _process_number(elements, section_title_name)
    }

    question = {
        'question_id': generate_id(section.get('section_title'), 'question', index),
        'question_title': _process_title(elements, 'question_title'),
        'question_description': _process_description(elements, 'question_description'),
        'question_guidance':  _process_question_guidance(elements),
        'question_number': _process_number(elements, 'question_title'),
        'answers': _process_answers(extracted.get('block_type'), section.get('section_title'), index, elements)
    }

    section.update(question)

    section['block_id'] = generate_id(section.get('section_title'), 'block', index)
    section['section_id'] = generate_id(section.get('section_title'), 'section', index)

    return section


def generate_id(*args):
    """
    Generate an id value from a list of arguments (lowercase with - separators)
    :param args: Arbitrary length list of arguments to form the id from
    :return: A str id value
    """
    _id = '-'.join([str(x) for x in args])
    _id = _id.lower()

    parts = re.sub('[^0-9a-zA-Z]+', '-', _id)
    return ''.join(parts)


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
        'id': generate_id(section_title, 'answer', index, '-', 0),
        'label': '',
        'description': '',
        'type': block_type,
        'mandatory': False,
        'q_code': '',
        'options': []
    }

    last_label_paragraph_index = -1
    last_option_paragraph_index = -1

    for element in filter(lambda x: x['type'].startswith('answer_'), elements):

        if element.get('type') == 'answer_label':
            if element.get('paragraph_index') == last_label_paragraph_index or not element.get('content').strip():
                answer['label'] += element.get('content')
            else:
                # New label, start a new answer set
                _strip_append_answer(answers, answer)
                last_label_paragraph_index = element.get('paragraph_index')
                answer = {
                    'id': generate_id(section_title, 'answer', index, '-', len(answers)),
                    'label': element.get('content'),
                    'description': '',
                    'type': block_type,
                    'mandatory': False,
                    'q_code': '',
                    'options': []
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

    # Catch the last answer
    _strip_append_answer(answers, answer)

    return answers


def _strip_append_answer(answers, answer):
    """
    Strip an answer and only append it to the answers list if it isn't empty
    :param answers: The list of answers to append to
    :param answer: The answer to strip and append
    """
    stripped_answer = {
        'label': answer.get('label').strip(),
        'description': answer.get('description').strip(),
        'options': [_strip_option(o) for o in answer.get('options')]
    }

    if any(stripped_answer.values()):
        stripped_answer['id'] = answer.get('id')
        stripped_answer['type'] = answer.get('type')
        stripped_answer['mandatory'] = answer.get('mandatory')
        stripped_answer['q_code'] = answer.get('q_code')
        answers.append(stripped_answer)


def _process_question_guidance(elements):
    """
    Loop through the guidance elements (assumes they are ordered by y-transform) and generate guidance JSON.

    :param elements: The list of elements for this block
    :return: A list of guidance (schema ready)
    """
    all_guidance = []
    guidance = {
        'title': '',
        'description': '',
        'list': []
    }

    last_list_paragraph_index = -1
    last_title_paragraph_index = -1

    for element in filter(lambda x: x['type'].startswith('question_guidance_'), elements):
        if element.get('type') == 'question_guidance_title':
            if element.get('paragraph_index') == last_title_paragraph_index or not element.get('content').strip():
                guidance['title'] += element.get('content')
            else:
                # This must be a new guidance section
                last_title_paragraph_index = element.get('paragraph_index')
                _strip_append_guidance(all_guidance, guidance)
                guidance = {
                    'title': element.get('content'),
                    'description': '',
                    'list': []
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

    # Catch the last guidance
    _strip_append_guidance(all_guidance, guidance)

    return all_guidance


def _strip_append_guidance(all_guidance, guidance):
    stripped_guidance = {
        'title': guidance.get('title').strip(),
        'description': guidance.get('description').strip(),
        'list': [x.strip() for x in guidance.get('list') if x.strip()]
    }

    if any(stripped_guidance.values()):
        all_guidance.append(stripped_guidance)


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


def _content_for_type_as_html_list(elements, _type):
    """
    Returns a list of strings that had a 'type' of _type with
    html formatting applied to each element.

    Note: new lines aren't processed by this function (they remain as \n)

    :param _type: The type of element (e.g. 'section_title')
    :return: A list of html formatted strings
    """
    filtered_elements = _filter_by_type(elements, _type)
    content = []

    for element in filtered_elements:
        html = _element_to_html(element)
        content.append(html)

    content = ''.join(content) if content else ''

    return content


def _element_to_html(element):
    """
    Converts a element to a HTML string, with its style converted to
    HTML tags.
    :param element: the element to convert to HTML
    :return: an HTML formatted str
    """
    style = element.get('style')
    content = element.get('content')

    if style and content:
        if _contains_colour_value(style.get('backgroundColor')):
            content = _safe_wrap_in_html_tag(content, 'em')

    return content


def _contains_colour_value(colour):
    """
    Returns whether a colour dict contains a colour value or is empty
    :param colour: The colour dict to check
    :return: True if there is a value associate with the colour, False otherwise
    """
    return bool(get_dict_nested_value(colour, 'opaqueColor', 'rgbColor'))


def _safe_wrap_in_html_tag(content, tag_name):
    """
    Adds an html tag around content but handles new line characters
    to prevent incorrectly nested tags later
    :param content: The content to wrap in the tag
    :param tag_name: The name of the tag to use e.g. 'em', 'strong'
    :return: the HTML tagged string
    """
    raw_lines = content.split('\n')
    tagged_lines = []
    for line in raw_lines:
        if line.strip():
            tagged_line = '<{tag_name}>{line}</{tag_name}>'.format(tag_name=tag_name, line=line)
            tagged_lines.append(tagged_line)
        else:
            tagged_lines.append(line)

    return '\n'.join(tagged_lines)


def _is_interstitial(elements):
    for interstitial in _filter_by_type(elements, 'interstitial_title'):
        if len(interstitial.get('content')) > 0:
            return True

    return False


def _clean_join(content):
    """
    Joins a list of values together and cleans (removes newlines)
    :param content: A str or list of str to process
    :return: The joined/cleaned str
    """
    if not isinstance(content, str):
        content = ''.join(content) if content else ''
    return content.replace('\n', '')


def _clean_join_with_html_paragraphs(content):
    """
    Joins a list of values together and replaces new lines
    with HTML <p> tags
    :param content: A str or list of str to process
    :return: The joined/cleaned str with <p> tags
    """
    if not isinstance(content, str):
        content = ''.join(content) if content else ''

    return _new_lines_to_html_paragraphs(content)


def _new_lines_to_html_paragraphs(content):
    """
    Converts new line characters to HTML <p> tags
    :param content: The content to convert
    :return: A HTML string with <p> tags for new lines
    """
    html = ''
    if content:
        paragraphs = content.split('\n')
        for paragraph in [x for x in paragraphs if x]:
            html += '<p>' + paragraph + '</p>'

    return html


def _process_title(elements, element_type):
    content = _content_for_type_as_html_list(elements, element_type)
    title = _clean_join(content)
    return _extract_title_number(title).get('title')


def _process_label(elements, element_type):
    content = _content_for_type_as_html_list(elements, element_type)
    return _clean_join(content)


def _process_number(elements, element_type):
    content = _content_for_type_as_html_list(elements, element_type)
    title = _clean_join(content)
    return _extract_title_number(title).get('number')


def _process_description(elements, element_type):
    content = _content_for_type_as_html_list(elements, element_type)
    return _clean_join_with_html_paragraphs(content)


def _process_option(content):
    """
    Converts content into a radio/checkbox option schema output
    :return: A dict ready for use in the JSON Schema as a radio/check option
    """
    val = _clean_join(content)
    return [{
        'label': val,
        'value': val,
        'q_code': ''
    }]


def _append_option(option, content):
    """
    Appends to an existing option with more content
    """
    val = _clean_join(content)
    option['label'] += val
    option['value'] += val


def _strip_option(option):
    """
    Strips an option dict
    """
    return {
        'label': option.get('label').strip(),
        'value': option.get('value').strip(),
        'q_code': option.get('q_code').strip()
    }


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
