from reviewlens.review.chunking import Chunk, chunk_file_diff

# A 30-line synthetic pre-review file, 1-indexed via FILE_LINES[n - 1].
FILE_LINES = [f"L{i}" for i in range(1, 31)]


def test_single_hunk_mid_file_expands_with_context():
    patch = "@@ -15,1 +15,1 @@\n-L15\n+L15-changed\n"
    chunks = chunk_file_diff("Foo.java", patch, context_lines=2, file_lines=FILE_LINES)

    assert chunks == [
        Chunk(
            file="Foo.java",
            start_line=13,
            end_line=17,
            content="\n".join(
                [
                    "  13: L13",
                    "  14: L14",
                    "- : L15",
                    "+ 15: L15-changed",
                    "  16: L16",
                    "  17: L17",
                ]
            ),
        )
    ]


def test_hunk_at_file_start_clamps():
    patch = "@@ -1,1 +1,1 @@\n-L1\n+L1-changed\n"
    file_lines = [f"L{i}" for i in range(1, 11)]
    chunks = chunk_file_diff("Foo.java", patch, context_lines=3, file_lines=file_lines)

    assert len(chunks) == 1
    assert chunks[0].start_line == 1  # clamped, can't go below line 1
    assert chunks[0].end_line == 4


def test_hunk_at_file_end_clamps():
    file_lines = [f"L{i}" for i in range(1, 11)]  # 10 lines
    patch = "@@ -10,1 +10,1 @@\n-L10\n+L10-changed\n"
    chunks = chunk_file_diff("Foo.java", patch, context_lines=3, file_lines=file_lines)

    assert len(chunks) == 1
    assert chunks[0].start_line == 7
    assert chunks[0].end_line == 10  # clamped, file has no line 13


def test_two_distant_hunks_stay_separate():
    patch = (
        "@@ -2,1 +2,1 @@\n"
        "-L2\n"
        "+L2-changed\n"
        "@@ -20,1 +20,1 @@\n"
        "-L20\n"
        "+L20-changed\n"
    )
    chunks = chunk_file_diff("Foo.java", patch, context_lines=1, file_lines=FILE_LINES)

    assert len(chunks) == 2
    assert (chunks[0].start_line, chunks[0].end_line) == (1, 3)
    assert (chunks[1].start_line, chunks[1].end_line) == (19, 21)


def test_overlapping_expanded_hunks_merge_into_one_chunk():
    patch = (
        "@@ -5,1 +5,1 @@\n"
        "-L5\n"
        "+L5-changed\n"
        "@@ -8,1 +8,1 @@\n"
        "-L8\n"
        "+L8-changed\n"
    )
    chunks = chunk_file_diff("Foo.java", patch, context_lines=2, file_lines=FILE_LINES)

    assert len(chunks) == 1
    assert chunks[0].start_line == 3
    assert chunks[0].end_line == 10
    # The gap between the two hunks (lines 6-7) is filled in as plain context.
    assert "  6: L6" in chunks[0].content
    assert "  7: L7" in chunks[0].content


def test_exactly_adjacent_hunks_merge_even_with_zero_context():
    patch = (
        "@@ -5,1 +5,1 @@\n"
        "-L5\n"
        "+L5-changed\n"
        "@@ -6,1 +6,1 @@\n"
        "-L6\n"
        "+L6-changed\n"
    )
    chunks = chunk_file_diff("Foo.java", patch, context_lines=0, file_lines=FILE_LINES)

    assert len(chunks) == 1
    assert chunks[0].start_line == 5
    assert chunks[0].end_line == 6
    assert chunks[0].content == "\n".join(
        ["- : L5", "+ 5: L5-changed", "- : L6", "+ 6: L6-changed"]
    )


def test_context_lines_zero_means_no_expansion():
    patch = "@@ -15,1 +15,1 @@\n-L15\n+L15-changed\n"
    chunks = chunk_file_diff("Foo.java", patch, context_lines=0, file_lines=FILE_LINES)

    assert len(chunks) == 1
    assert chunks[0].start_line == 15
    assert chunks[0].end_line == 15
    assert chunks[0].content == "- : L15\n+ 15: L15-changed"


def test_hunk_header_without_counts_defaults_to_one():
    patch = "@@ -1 +1 @@\n-old\n+new\n"
    chunks = chunk_file_diff("Foo.java", patch, context_lines=0)

    assert len(chunks) == 1
    assert chunks[0].start_line == 1
    assert chunks[0].end_line == 1
    assert chunks[0].content == "- : old\n+ 1: new"


def test_new_file_diff_has_no_expansion_without_file_lines():
    patch = "@@ -0,0 +1,3 @@\n+line1\n+line2\n+line3\n"
    # No pre-review content exists for a brand-new file.
    chunks = chunk_file_diff("New.java", patch, context_lines=5, file_lines=None)

    assert len(chunks) == 1
    assert chunks[0].start_line == 1
    assert chunks[0].end_line == 3
    assert chunks[0].content == "\n".join(["+ 1: line1", "+ 2: line2", "+ 3: line3"])
