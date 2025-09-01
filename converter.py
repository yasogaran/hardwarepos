import flet as ft


class HTML:
    # ----------------------------------------------------------------------------------------------
    """
    supported HTML tags and attributes
    """

    html_tags = [
        "ul",
        "ol",
        "li",
        "img",
        "a",
        "b",
        "strong",
        "i",
        "em",
        "u",
        "mark",
        "span",
        "div",
        "p",
        "pre",
        "code",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "table",
        "tr",
        "th",
        "td",
    ]

    class Attrs:
        STYLE = "style"
        HREF = "href"
        SRC = ""
        WIDTH = "width"
        HEIGHT = "height"
        TYPE = "type"

    style_attributes = [
        "color",
        "background-color",
        "font-family",
        "font-size",
        "font-weight",
        "font-style",
        "text-align",
        "text-decoration",
        "box-shadow",
        "line-height",
        "letter-spacing",
        "word-spacing",
        "overflow",
        "position",
        "top",
        "right",
        "bottom",
        "left",
    ]

    TEXT_STYLE_DECORATION = ["underline", "line-through", "overline"]

    HEADINGS_TEXT_SIZE = {
        "h1": 32,
        "h2": 24,
        "h3": 18,
        "h4": 16,
        "h5": 13,
        "h6": 10,
    }


def parse_html_to_flet(element):
    if element.name == "div":
        style, align_style = get_style(element, is_a_mapping=True)
        print(align_style)
        # Map <div> to ft.Column
        main_container = ft.Container(
            content=ft.Row([], **align_style)
            if "alignment" in align_style
            else ft.Column([]),
            **style,
        )
        for child in element.children:
            if child.name:
                # If there's a table,
                if child.name == "table":
                    # Call "html_table_to_flet()" function to display the table
                    html_table_to_flet(element, main_container)
                # Recursively parse child elements
                child_flet = parse_html_to_flet(child)
                main_container.content.controls.append(child_flet)
        return main_container

    # Heading tags
    elif element.name in HTML.HEADINGS_TEXT_SIZE.keys():
        heading_text = ft.Text(
            value=element.text, size=HTML.HEADINGS_TEXT_SIZE[element.name]
        )
        return heading_text
    # Paragraph tag
    elif element.name == "p":
        # Map <p> to ft.Text within ft.Row
        style = get_style(element)
        paragraph = ft.Row([ft.Text(spans=[ft.TextSpan(element.text, style=style[0])])])

        # Support for nested tags inside the <p> tag ##STILL NEED IMPROVEMENTS

        if element.children:
            for child in element.children:
                if child.name:
                    # Parse the nested element
                    p_child = parse_html_to_flet(child)

                    # Find the start index of nested element's text
                    start_index = paragraph.controls[0].spans[0].text.find(child.text)

                    # Remove nested element's text from the main paragraph text
                    paragraph.controls[0].spans[0].text = (
                        paragraph.controls[0].spans[0].text.replace(child.text, "")
                    )
                    # Retrieve the rest of the main paragraph text
                    rest_ = paragraph.controls[0].spans[0].text[start_index:]

                    # Remove the rest of the main paragraph text after the start index, to get the text before the nested element
                    paragraph.controls[0].spans[0].text = (
                        paragraph.controls[0].spans[0].text[:start_index]
                    )
                    # Create a new text element for the rest of the main paragraph text
                    rest_text = ft.Text(spans=[ft.TextSpan(rest_, style=style[0])])

                    # Add the nested element and the rest of the paragraph text to the MainParagraph
                    paragraph.controls.extend([p_child, rest_text])

        return paragraph
    # Link tag
    elif element.name == "a":
        # Map <a> to ft.Text with a URL
        link = ft.Text(
            spans=[
                ft.TextSpan(
                    element.text,
                    url=element.get(HTML.Attrs.HREF),
                    style=ft.TextStyle(italic=True, color="blue"),
                )
            ]
        )
        return link

    # Image tag
    elif element.name == "img":
        img_style, _ = get_style(element, is_a_mapping=True)

        # Map <img> to ft.Image with a source URL
        image = ft.Container(
            content=ft.Image(src=element.get(HTML.Attrs.SRC)), **img_style
        )
        return image

    # HTML lists

    elif element.name == "ul" or element.name == "ol":
        # Map <ul> and <ol> to ft.Column or ft.Row with ft.Text elements
        list_container = ft.Column(spacing=0)

        for i, li in enumerate(element.find_all("li")):
            _leading = (
                ft.Text("•", size=20)
                if element.name == "ul"
                else ft.Text(f"{i + 1}", size=16)
            )
            list_item = ft.ListTile(title=ft.Text(li.text), leading=_leading)

            list_container.controls.append(list_item)
        return list_container
    # Bold Tags
    elif element.name == "b" or element.name == "strong":
        bold_text = ft.Text(
            value=element.text,
            weight=ft.FontWeight.BOLD if element.name == "b" else ft.FontWeight.W_900,
        )
        return bold_text
    # Italic Tag
    elif element.name == "i" or element.name == "em":
        italic_text = ft.Text(element.text, italic=True)
        return italic_text
    # Underline Tag
    elif element.name == "u":
        underlined_text = ft.Text(
            spans=[
                ft.TextSpan(
                    element.text,
                    style=ft.TextStyle(decoration=ft.TextDecoration.UNDERLINE),
                )
            ]
        )
        return underlined_text
    # mark Tag
    elif element.name == "mark":
        style_props, _ = get_style(element, is_a_mapping=True)

        return ft.Text(
            spans=[
                ft.TextSpan(
                    element.text,
                    style=ft.TextStyle(**style_props),
                )
            ]
        )
    # Code Tag
    elif element.name == "code":
        return ft.Markdown(
            element.text,
            selectable=True,
            extension_set="gitHubWeb",
            code_theme="atom-one-dark",
        )

    else:
        # Default to ft.Container for unrecognized elements
        container = ft.Container()
        for child in element.children:
            if child.name:
                child_flet = parse_html_to_flet(child)
                container.content = child_flet
        return container


# ____________________________________________________________________________________________________________________________________
# Parser function for html tables


def html_table_to_flet(element, container):
    table = element.find("table", border="1")
    flet_table = ft.DataTable(columns=[], rows=[])

    if table != None:
        for row in table.find_all("tr"):
            headers = row.find_all("th")
            columns = row.find_all("td")
            if headers != []:
                for i in range(len(headers)):
                    header_text = headers[i].text
                    flet_table.columns.append(ft.DataColumn(ft.Text(header_text)))

            if columns != []:
                data_cells = []
                for i in range(len(columns)):
                    cell_text = columns[i].text
                    data_cells.append(ft.DataCell(ft.Text(cell_text)))
                flet_table.rows.append(ft.DataRow(cells=data_cells))
        container.content.controls.append(flet_table)


# ___________________________________________________________________________________________________________________________________
# Associate html inline styles to the corresponding flet style properties
# ____________________________________________________________________________________________________________________________________
html_to_flet_style_mapping = {
    "color": "color",
    "background-color": "bgcolor",
    "font-family": "font_family",
    "font-size": "size",
    "text-align": "text_align",
    "text-decoration": "decoration",
    "padding": "padding",
    "display": "display",
    "justify-content": "alignment",
    "margin": "margin",
    "border-radius": "border_radius",
    "border": "border",
    "width": "width",
    "height": "height",
}


def parse_inline_styles(style_string):
    # Parse inline styles and convert to Flet properties
    style_properties = {}
    for style_declaration in style_string.split(";"):
        if ":" in style_declaration:
            property_name, property_value = style_declaration.split(":")
            property_name = property_name.strip()
            property_value = property_value.strip()

            # Convert property_name to Flet style name if needed
            property_name = html_to_flet_style_mapping.get(property_name, None)

            if property_name:
                deco_values = {
                    "underline": ft.TextDecoration.UNDERLINE,
                    "line-through": ft.TextDecoration.LINE_THROUGH,
                    "overline": ft.TextDecoration.OVERLINE,
                }

                alignment_values = {
                    "flex-start": ft.MainAxisAlignment.START,
                    "center": ft.MainAxisAlignment.CENTER,
                    "flex-end": ft.MainAxisAlignment.END,
                    "space-between": ft.MainAxisAlignment.SPACE_BETWEEN,
                    "space-around": ft.MainAxisAlignment.SPACE_AROUND,
                    "space-evenly": ft.MainAxisAlignment.SPACE_EVENLY,
                }

                style_properties[property_name] = (
                    int(property_value) if property_value.isdigit() else property_value
                )
                # handle decoration property
                if property_name == "decoration" and property_value in deco_values:
                    style_properties["decoration"] = deco_values[property_value]
                # handle border property
                elif property_name == "border" and property_value != None:
                    property_value = property_value.split(" ")
                    style_properties["border"] = ft.border.all(
                        property_value[0], property_value[-1]
                    )
                elif (
                        property_name == "alignment" and property_value in alignment_values
                ):
                    style_properties["alignment"] = alignment_values[property_value]
    style_properties.pop("display", None)

    return style_properties


def get_style(element, is_a_mapping: bool = False):
    alignment_props = {}
    if element.get(HTML.Attrs.STYLE):
        style_props = parse_inline_styles(element.get(HTML.Attrs.STYLE))
        if "alignment" in style_props:
            val = style_props.pop("alignment")
            alignment_props = {"alignment": val}
        # else:
        #     alignment_props = {}
        _style = style_props if is_a_mapping else ft.TextStyle(**style_props)

    else:
        _style = {}
    return _style, alignment_props
