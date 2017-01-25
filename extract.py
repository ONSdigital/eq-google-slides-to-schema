from utils import get_dict_nested_value


def extract_content(slide):
    elements = slide.get('pageElements')

    print('{} elements'.format(len(elements)))

    extracted = {
        'elements': [],
        'answer_type': ''
    }

    skip = False
    checkbox = False
    radio = False
    currency = False
    comments = False
    interstitial = False
    paragraph_marker = None
    paragraph_index = 0

    for element in (e for e in elements if 'shape' in e):
        shape = element.get('shape')
        transform = element.get('transform')

        if _skip_slide(shape):
            skip = True
            break

        elif _is_text(shape):
            for text_element in shape.get('text').get('textElements'):
                if 'paragraphMarker' in text_element:
                    paragraph_index += 1
                    paragraph_marker = text_element.get('paragraphMarker')

                if 'textRun' in text_element:
                    _content = text_element.get('textRun').get('content')
                    _style = text_element.get('textRun').get('style')
                    _type = _get_type(_content, _style, paragraph_marker)

                    interstitial |= _type == 'interstitial_title'

                    extracted['elements'].append(
                        {
                            'paragraph_index': paragraph_index,
                            'paragraph_marker': paragraph_marker,
                            'content': _content,
                            'style': _style,
                            'transform': transform,
                            'type': _type
                        }
                    )

        elif _is_checkbox(shape):
            checkbox |= True

        elif _is_radio(shape):
            radio |= True

        elif _is_currency(shape):
            currency |= True

        elif _is_comments_box(shape):
            comments |= True

    if interstitial:
        extracted['block_type'] = 'Interstitial'
    elif checkbox:
        extracted['block_type'] = 'Checkbox'
    elif radio:
        extracted['block_type'] = 'Radio'
    elif currency:
        extracted['block_type'] = 'Currency'
    elif comments:
        extracted['block_type'] = 'TextArea'
    else:
        extracted['block_type'] = 'PositiveInteger'

    return extracted if not skip else None


def _get_type(content, style, paragraph_marker):

    if _ignore_text(content, style):
        element_type = 'ignored'
    elif _is_interstitial_title(style):
        element_type = 'interstitial_title'
    elif _is_interstitial_description(style):
        element_type = 'interstitial_description'
    elif _is_section_title(style):
        element_type = 'section_title'
    elif _is_section_description(style):
        element_type = 'section_description'
    elif _is_question_title(style):
        element_type = 'question_title'
    elif _is_question_guidance_title(style, paragraph_marker):
        element_type = 'question_guidance_title'
    elif _is_question_guidance_description(style, paragraph_marker):
        element_type = 'question_guidance_description'
    elif _is_question_guidance_list(style, paragraph_marker):
        element_type = 'question_guidance_list'
    elif _is_question_description(style):
        element_type = 'question_description'
    elif _is_answer_label(style):
        element_type = 'answer_label'
    elif _is_answer_prompt(style):
        element_type = 'answer_prompt'
    elif _is_answer_option(style):
        element_type = 'answer_option'
    elif _is_answer_further_guidance(style):
        element_type = 'answer_further_guidance'
    elif _is_answer_q_code(style):
        element_type = 'answer_q_code'
    else:
        element_type = 'ignored'

    return element_type


def _skip_slide(shape):
    """ Checks if this shape indicates this slide should be Skipped; a NO_SMOKING shape on them """
    return shape.get('shapeType') == 'NO_SMOKING'


def _is_text(shape):
    """ Checks if this shape represents text content; a TEXT_BOX """
    return shape.get('shapeType') == 'TEXT_BOX' and 'text' in shape


def _is_checkbox(shape):
    """ Checks if this shape represents a Checkbox question; a RECTANGLE with a red outline """
    if shape.get('shapeType') != 'RECTANGLE':
        return False

    color = get_dict_nested_value(shape, 'shapeProperties', 'outline', 'outlineFill', 'solidFill', 'color', 'rgbColor')

    return 'blue' not in color and 'green' not in color and 'red' in color and color.get('red') == 1


def _is_comments_box(shape):
    """ Checks if this shape represents a Comments question; RECTANGLE with a green outline """
    if shape.get('shapeType') != 'RECTANGLE':
        return False

    color = get_dict_nested_value(shape, 'shapeProperties', 'outline', 'outlineFill', 'solidFill', 'color', 'rgbColor')

    return 'blue' not in color and 'red' not in color and 'green' in color and color.get('green') == 1


def _is_radio(shape):
    """ Checks if this shape represents a Radio question; an ELLIPSE/circle """
    return shape.get('shapeType') == 'ELLIPSE'


def _is_currency(shape):
    """ Check if this shape represents a Currency question; a 'ROUND_RECTANGLE' """
    return shape.get('shapeType') == 'ROUND_RECTANGLE'


def _ignore_text(content, style):
    """ Check if this content should be ignored; i.e. isn't BLACK text """
    if not content:
        return True

    rgb_color = get_dict_nested_value(style, 'foregroundColor', 'opaqueColor', 'rgbColor')

    if not rgb_color or len(rgb_color) == 0:
        return False
    else:
        return True


def _is_interstitial_title(style):
    return _is_font_size(style, 30)


def _is_interstitial_description(style):
    return _is_font_size(style, 28)


def _is_section_title(style):
    return _is_font_size(style, 24)


def _is_section_description(style):
    return _is_font_size(style, 22)


def _is_question_title(style):
    return _is_font_size(style, 20)


def _is_question_description(style):
    return _is_font_size(style, 18)


def _is_question_guidance_title(style, paragraph_marker):
    return _is_font_size(style, 16) and _is_font_bold(style) and not _is_paragraph_bullet_list(paragraph_marker)


def _is_question_guidance_description(style, paragraph_marker):
    return _is_font_size(style, 16) and not _is_paragraph_bullet_list(paragraph_marker)


def _is_question_guidance_list(style, paragraph_marker):
    return _is_font_size(style, 16) and _is_paragraph_bullet_list(paragraph_marker)


def _is_answer_label(style):
    return _is_font_size(style, 14)


def _is_answer_option(style):
    return _is_font_size(style, 13)


def _is_answer_prompt(style):
    return _is_font_size(style, 12)


def _is_answer_further_guidance(style):
    return _is_font_size(style, 11)


def _is_answer_q_code(style):
    return _is_font_size(style, 9)


def _is_font_size(style, size):
    return get_dict_nested_value(style, 'fontSize', 'magnitude') == size


def _is_font_bold(style):
    return style and style.get('bold')


def _is_paragraph_bullet_list(paragraph_marker):
    return paragraph_marker and paragraph_marker.get('bullet') is not None
