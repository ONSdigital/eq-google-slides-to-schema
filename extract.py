
def extract_content(slide):
    elements = slide.get('pageElements')

    print("{} elements".format(len(elements)))

    extracted = {
        "elements": [],
        "answer_type": ""
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

                    extracted["elements"].append(
                        {
                            "paragraph_index": paragraph_index,
                            "content": _content,
                            "style": _style,
                            "transform": transform,
                            "type": _type
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
    else:
        element_type = 'ignored'

    return element_type


def _skip_slide(shape):
    """
    Skip any slides that have the 'NO_SMOKING' shape on them
    """
    return shape.get('shapeType') == 'NO_SMOKING'


def _is_text(shape):
    if shape.get('shapeType') != 'TEXT_BOX':
        return False

    return 'text' in shape


def _is_checkbox(shape):
    """ Checks if this shape has a red outline"""
    if shape.get('shapeType') != 'RECTANGLE':
        return False

    color = shape.get(
        'shapeProperties', {}).get(
        'outline', {}).get(
        'outlineFill', {}).get(
        'solidFill', {}).get(
        'color', {}).get(
        'rgbColor')

    return 'blue' not in color and 'green' not in color and 'red' in color and color.get('red') == 1


def _is_comments_box(shape):
    """ Checks if this shape has a green outline"""
    if shape.get('shapeType') != 'RECTANGLE':
        return False

    color = shape.get(
        'shapeProperties', {}).get(
        'outline', {}).get(
        'outlineFill', {}).get(
        'solidFill', {}).get(
        'color', {}).get(
        'rgbColor')

    return 'blue' not in color and 'red' not in color and 'green' in color and color.get('green') == 1


def _is_radio(shape):
    """ Checks if this shape is a circle"""
    return shape.get('shapeType') == 'ELLIPSE'


def _is_currency(shape):
    """
    Currency questions have a 'ROUND_RECTANGLE' shape on them
    """
    return shape.get('shapeType') == 'ROUND_RECTANGLE'


def _ignore_text(content, style):
    if not content:
        return True

    if 'foregroundColor' not in style:
        return False

    if 'opaqueColor' not in style.get('foregroundColor'):
        return False

    color = style.get('foregroundColor').get('opaqueColor')
    if 'rgbColor' not in color:
        return False

    if len(color.get('rgbColor')) == 0:
        return False

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


def _is_font_size(style, size):
    if not style:
        return False

    font_size = style.get('fontSize', {}).get('magnitude')
    return font_size == size


def _is_font_bold(style):
    if not style:
        return False

    return style.get('bold')


def _is_paragraph_bullet_list(paragraph_marker):
    if not paragraph_marker:
        return False

    bullet = paragraph_marker.get('bullet') is not None
    return bullet
