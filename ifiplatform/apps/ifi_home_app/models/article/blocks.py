"""StreamField block factories for article body content and
StudentUnionCategoryPage's union_groups -- leaves with no dependency on any
page model. Functions, not shared instances, since Wagtail block instances
aren't safe to reuse across multiple StreamField/StreamBlock definitions.

Design rationale/history: docs/claude_context/article_blocks.md"""

from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock


def article_image_block():
    """A single image with an optional caption. Layout/box styling lives
    only in ArticleBlockStyle, edited on-page via editor mode."""
    return blocks.StructBlock(
        [
            ("image", ImageChooserBlock()),
            (
                "alt_text",
                blocks.CharBlock(
                    required=False,
                    help_text="Accessible description. Leave blank to use the image's own title.",
                ),
            ),
            ("caption", blocks.CharBlock(required=False)),
        ],
        icon="image",
    )


def article_paragraph_block():
    """A rich text block. See docs/claude_context/article_blocks.md for
    why this is a StructBlock, not a bare RichTextBlock."""
    return blocks.StructBlock(
        [
            ("text", blocks.RichTextBlock()),
        ],
        icon="pilcrow",
        label="Paragraph",
    )


def article_card_block():
    """Embeds another ArticlePage as a homepage-style card."""
    return blocks.StructBlock(
        [
            (
                "article",
                blocks.PageChooserBlock(
                    page_type="ifi_home_app.ArticlePage",
                    required=True,
                    help_text="The article to recommend.",
                ),
            ),
        ],
        icon="doc-full",
        label="Article Card",
    )


def category_card_block():
    """Embeds a CategoryPage as a small accent-colored tile."""
    return blocks.StructBlock(
        [
            (
                "category",
                blocks.PageChooserBlock(
                    page_type="ifi_home_app.CategoryPage",
                    required=True,
                    help_text="The category to link to.",
                ),
            ),
        ],
        icon="tag",
        label="Category Card",
    )


def union_card_block():
    """Embeds a UnionPage as a round-logo card."""
    return blocks.StructBlock(
        [
            (
                "union",
                blocks.PageChooserBlock(
                    page_type="ifi_home_app.UnionPage",
                    required=True,
                    help_text="The student union to link to.",
                ),
            ),
        ],
        icon="group",
        label="Student Union Card",
    )


def union_group_block():
    """One titled group of union cards (see
    StudentUnionCategoryPage.union_groups) -- used standalone or nested in
    a "row" of several groups shown side by side."""
    return blocks.StructBlock(
        [
            (
                "title",
                blocks.CharBlock(
                    required=True,
                    help_text="Group heading, e.g. 'Faglige foreninger'.",
                ),
            ),
            (
                "general_info",
                blocks.RichTextBlock(
                    required=False,
                    help_text="Optional -- a short paragraph about this group, shown below its title.",
                ),
            ),
            (
                "unions",
                blocks.ListBlock(
                    union_card_block(),
                    help_text="Student unions in this group.",
                ),
            ),
        ],
        icon="group",
        label="Union group",
    )


def tool_card_block():
    """Embeds a ToolPage as an image+maker card."""
    return blocks.StructBlock(
        [
            (
                "tool",
                blocks.PageChooserBlock(
                    page_type="ifi_home_app.ToolPage",
                    required=True,
                    help_text="The tool to link to.",
                ),
            ),
        ],
        icon="cog",
        label="Tool Card",
    )


def _body_content_blocks():
    """The block types available at the top level of an article body."""
    return [
        (
            "heading",
            blocks.StructBlock(
                [
                    ("text", blocks.CharBlock()),
                    (
                        "level",
                        blocks.ChoiceBlock(
                            choices=[
                                ("h2", "Level 1"),
                                ("h3", "Level 2"),
                                ("h4", "Level 3"),
                                ("h5", "Level 4"),
                            ],
                            default="h2",
                            label="Subsection level",
                            help_text=(
                                "How deep this heading nests in the article's "
                                "structure -- drives both its size and its "
                                "indentation in the table of contents. Stored as "
                                "an HTML heading tag (h2-h5) under the hood, but "
                                "shown here as a plain nesting depth since the "
                                "actual tag doesn't matter to editors."
                            ),
                        ),
                    ),
                ]
            ),
        ),
        ("paragraph", article_paragraph_block()),
        (
            "multi_column",
            blocks.StructBlock(
                [
                    (
                        "columns",
                        blocks.ListBlock(
                            blocks.StructBlock(
                                [
                                    ("title", blocks.CharBlock(required=False)),
                                    (
                                        "content",
                                        blocks.StreamBlock(
                                            [
                                                (
                                                    "paragraph",
                                                    article_paragraph_block(),
                                                ),
                                                ("image", article_image_block()),
                                                ("article_card", article_card_block()),
                                                (
                                                    "category_card",
                                                    category_card_block(),
                                                ),
                                                ("union_card", union_card_block()),
                                                ("tool_card", tool_card_block()),
                                            ],
                                            required=False,
                                        ),
                                    ),
                                ]
                            ),
                            min_num=1,
                            max_num=4,
                            label="Column",
                        ),
                    ),
                    (
                        "column_alignment",
                        blocks.ChoiceBlock(
                            choices=[
                                ("top", "Top"),
                                ("center", "Center"),
                                ("bottom", "Bottom"),
                            ],
                            default="top",
                            help_text=(
                                "Only matters if columns end up different heights "
                                "(more text, a bigger letter size, or an image in "
                                "one but not another). Decides where the shorter "
                                "column's empty space goes: below it (Top), split "
                                "above and below (Center), or above it (Bottom)."
                            ),
                        ),
                    ),
                ],
                icon="placeholder",
                label="Multi-column Text",
            ),
        ),
        ("image", article_image_block()),
        ("article_card", article_card_block()),
        ("category_card", category_card_block()),
        ("union_card", union_card_block()),
        ("tool_card", tool_card_block()),
    ]


def _iter_toc_entries(body_stream):
    """Recursively walks a body StreamValue yielding (level, text) pairs
    for the table of contents: top-level headings, and multi_column column
    titles (treated as h3s). See docs/claude_context/article_blocks.md."""
    for block in body_stream:
        if block.block_type == "heading":
            yield block.value["level"], block.value["text"]
        elif block.block_type == "multi_column":
            for column in block.value["columns"]:
                if column.get("title"):
                    yield "h3", column["title"]
