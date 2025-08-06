"""
Property-based tests for the markdown_converter module.
"""
import unittest
from hypothesis import given, strategies as st, settings

from src.youtube_notion.utils.markdown_converter import parse_rich_text, markdown_to_notion_blocks

# Hypothesis profile for faster feedback
settings.register_profile("ci", max_examples=1000)
settings.load_profile("ci")

# A strategy for generating text that does not contain markdown control characters
plain_text = st.text(st.characters(exclude_characters='*~`[]()|\n\r\x0c\x0b\t'), min_size=1)

# A strategy for generating markdown-like text with bold, italic, and strikethrough.
# This is a recursive strategy that builds up more complex strings from simpler ones.
markdown_text = st.recursive(
    plain_text,
    lambda children: st.one_of(
        children,
        st.builds(lambda s: f"**{s}**", children),
        st.builds(lambda s: f"*{s}*", children),
        st.builds(lambda s: f"~~{s}~~", children),
    )
)

# Strategy for generating valid URLs
url_strategy = st.builds(
    lambda domain, path: f"https://{domain}/{path}",
    st.text(st.characters(min_codepoint=97, max_codepoint=122), min_size=3),
    st.text(st.characters(min_codepoint=97, max_codepoint=122), min_size=3)
)

# Strategy for generating markdown links
link_strategy = st.builds(
    lambda text, url: f"[{text}]({url})",
    plain_text,
    url_strategy
)

# Strategy for generating code blocks
code_block_strategy = st.builds(
    lambda code: f"```\n{code}\n```",
    st.text(st.characters(exclude_characters='`'))
)

# Strategy for generating table rows
@st.composite
def table_strategy(draw):
    num_cols = draw(st.integers(min_value=1, max_value=5))
    header_cells = draw(st.lists(plain_text, min_size=num_cols, max_size=num_cols))
    header = f"| {' | '.join(header_cells)} |"
    separator = f"|{'---|' * num_cols}"
    rows = draw(st.lists(
        st.lists(plain_text, min_size=num_cols, max_size=num_cols).map(
            lambda row: f"| {' | '.join(row)} |"
        ),
        min_size=1,
        max_size=4
    ))
    return "\n".join([header, separator] + rows)


class TestParseRichTextPropertyBased(unittest.TestCase):

    @given(st.text())
    def test_does_not_crash(self, text):
        """
        Test that parse_rich_text does not crash on any unicode text input.
        """
        try:
            parse_rich_text(text)
        except Exception as e:
            self.fail(f"parse_rich_text crashed with exception {e} on input: {text!r}")

    @given(st.text())
    def test_output_is_list_of_dicts(self, text):
        """
        Test that the output is always a list of dictionaries.
        """
        result = parse_rich_text(text)
        self.assertIsInstance(result, list)
        for item in result:
            self.assertIsInstance(item, dict)
            self.assertIn('type', item)
            self.assertEqual(item['type'], 'text')
            self.assertIn('text', item)
            self.assertIn('content', item['text'])

    @given(plain_text)
    def test_plain_text_is_preserved(self, text):
        """
        Test that plain text (without any markdown characters) is preserved.
        """
        result = parse_rich_text(text)
        if not text:
            self.assertEqual(result, [])
        else:
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]['text']['content'], text)
            self.assertNotIn('annotations', result[0])
            self.assertNotIn('link', result[0]['text'])

    @given(markdown_text)
    def test_markdown_structure_is_plausible(self, text):
        """
        Test that the parsed markdown structure is plausible.
        This test checks that the total length of the content in the parsed
        structure is consistent with the original text, and that annotations
        are applied correctly.
        """
        result = parse_rich_text(text)

        reconstructed_length = 0
        for item in result:
            reconstructed_length += len(item['text']['content'])
            # Check that annotations are boolean if they exist
            if 'annotations' in item:
                for key in ['bold', 'italic', 'strikethrough', 'code']:
                    if key in item['annotations']:
                        self.assertIsInstance(item['annotations'][key], bool)

        # The length of the reconstructed text should be less than or equal to the original text,
        # because the markdown characters are removed.
        self.assertLessEqual(reconstructed_length, len(text))

    @given(link_strategy)
    def test_link_is_parsed_correctly(self, text):
        """Test that a markdown link is parsed into a link component."""
        result = parse_rich_text(text)
        self.assertEqual(len(result), 1)
        self.assertIn('link', result[0]['text'])
        self.assertIn('url', result[0]['text']['link'])

    @given(code_block_strategy)
    def test_code_block_is_parsed_correctly(self, text):
        """Test that a code block is parsed into a code block component."""
        result = markdown_to_notion_blocks(text)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['type'], 'code')

    @given(table_strategy().filter(lambda x: all(c.strip() for c in x.split('\n')[0].split('|')[1:-1])).filter(lambda x: all(c.strip() for row in x.split('\n')[2:] for c in row.split('|')[1:-1])))
    def test_table_is_parsed_correctly(self, text):
        """Test that a markdown table is parsed into a table component."""
        result = markdown_to_notion_blocks(text)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['type'], 'table')

        table_block = result[0]['table']

        # Validate the table structure
        rows = text.split('\n')
        header_cells = [h.strip() for h in rows[0].split('|')[1:-1]]

        self.assertEqual(table_block['table_width'], len(header_cells))
        self.assertEqual(len(table_block['children']), len(rows) - 1)

        for i, row in enumerate(table_block['children']):
            self.assertEqual(len(row['table_row']['cells']), len(header_cells))
            for j, cell in enumerate(row['table_row']['cells']):
                original_text = rows[i if i == 0 else i + 1].split('|')[1:-1][j].strip()
                self.assertEqual(cell[0]['text']['content'], original_text)

if __name__ == '__main__':
    unittest.main()
