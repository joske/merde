use crate::myers::{DiffChunk, DiffTag};

/// Collect non-Equal chunks from both diffs, sorted by middle-file line position.
/// Returns (`chunk_index`, `is_right_diff`) pairs.
///
/// In the left diff, A = left file and B = middle file, so `start_b` gives the
/// middle-file line.  In the right diff, A = middle file and B = right file, so
/// `start_a` gives the middle-file line.
pub fn merge_change_indices(
    left_chunks: &[DiffChunk],
    right_chunks: &[DiffChunk],
) -> Vec<(usize, bool)> {
    let mut indices: Vec<(usize, bool, usize)> = Vec::new();
    for (i, c) in left_chunks.iter().enumerate() {
        if c.tag != DiffTag::Equal {
            indices.push((i, false, c.start_b));
        }
    }
    for (i, c) in right_chunks.iter().enumerate() {
        if c.tag != DiffTag::Equal {
            indices.push((i, true, c.start_a));
        }
    }
    indices.sort_by_key(|&(_, _, line)| line);
    indices
        .into_iter()
        .map(|(i, is_right, _)| (i, is_right))
        .collect()
}

/// Find 0-indexed line numbers of `<<<<<<<` conflict markers in the given text.
///
/// A line is considered a conflict marker only if it *starts with* `<<<<<<<`.
pub fn find_conflict_markers_in_text(text: &str) -> Vec<usize> {
    text.lines()
        .enumerate()
        .filter_map(|(i, line)| {
            if line.starts_with("<<<<<<<") {
                Some(i)
            } else {
                None
            }
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    // ── merge_change_indices ─────────────────────────────────────

    #[test]
    fn change_indices_empty() {
        let result = merge_change_indices(&[], &[]);
        assert!(result.is_empty());
    }

    #[test]
    fn change_indices_only_equal() {
        let left = vec![DiffChunk {
            tag: DiffTag::Equal,
            start_a: 0,
            end_a: 5,
            start_b: 0,
            end_b: 5,
        }];
        let right = left.clone();
        let result = merge_change_indices(&left, &right);
        assert!(result.is_empty());
    }

    #[test]
    fn change_indices_left_only() {
        let left = vec![
            DiffChunk {
                tag: DiffTag::Equal,
                start_a: 0,
                end_a: 2,
                start_b: 0,
                end_b: 2,
            },
            DiffChunk {
                tag: DiffTag::Replace,
                start_a: 2,
                end_a: 4,
                start_b: 2,
                end_b: 4,
            },
        ];
        let result = merge_change_indices(&left, &[]);
        assert_eq!(result, vec![(1, false)]);
    }

    #[test]
    fn change_indices_right_only() {
        let right = vec![
            DiffChunk {
                tag: DiffTag::Equal,
                start_a: 0,
                end_a: 3,
                start_b: 0,
                end_b: 3,
            },
            DiffChunk {
                tag: DiffTag::Delete,
                start_a: 3,
                end_a: 5,
                start_b: 3,
                end_b: 3,
            },
        ];
        let result = merge_change_indices(&[], &right);
        assert_eq!(result, vec![(1, true)]);
    }

    #[test]
    fn change_indices_sorted_by_middle_line() {
        let left = vec![DiffChunk {
            tag: DiffTag::Replace,
            start_a: 0,
            end_a: 2,
            start_b: 10, // middle line 10
            end_b: 12,
        }];
        let right = vec![DiffChunk {
            tag: DiffTag::Insert,
            start_a: 5, // middle line 5
            end_a: 5,
            start_b: 0,
            end_b: 2,
        }];
        let result = merge_change_indices(&left, &right);
        assert_eq!(result, vec![(0, true), (0, false)]);
    }

    #[test]
    fn change_indices_mixed_tags() {
        let left = vec![
            DiffChunk {
                tag: DiffTag::Insert,
                start_a: 0,
                end_a: 0,
                start_b: 0, // middle line 0
                end_b: 2,
            },
            DiffChunk {
                tag: DiffTag::Equal,
                start_a: 0,
                end_a: 5,
                start_b: 2,
                end_b: 7,
            },
            DiffChunk {
                tag: DiffTag::Delete,
                start_a: 5,
                end_a: 8,
                start_b: 7, // middle line 7
                end_b: 7,
            },
        ];
        let right = vec![DiffChunk {
            tag: DiffTag::Replace,
            start_a: 3, // middle line 3
            end_a: 5,
            start_b: 3,
            end_b: 6,
        }];
        let result = merge_change_indices(&left, &right);
        // Sorted: left[0] middle=0, right[0] middle=3, left[2] middle=7
        assert_eq!(result, vec![(0, false), (0, true), (2, false)]);
    }

    // ── find_conflict_markers_in_text ────────────────────────────

    #[test]
    fn conflict_markers_empty_text() {
        let result = find_conflict_markers_in_text("");
        assert!(result.is_empty());
    }

    #[test]
    fn conflict_markers_none_present() {
        let text = "line one\nline two\nline three\n";
        let result = find_conflict_markers_in_text(text);
        assert!(result.is_empty());
    }

    #[test]
    fn conflict_markers_single() {
        let text =
            "before\n<<<<<<< HEAD\nconflict content\n=======\nother side\n>>>>>>> branch\nafter\n";
        let result = find_conflict_markers_in_text(text);
        assert_eq!(result, vec![1]);
    }

    #[test]
    fn conflict_markers_multiple() {
        let text = "<<<<<<< HEAD\nfoo\n=======\nbar\n>>>>>>> b\n<<<<<<< HEAD\nbaz\n=======\nqux\n>>>>>>> b\n";
        let result = find_conflict_markers_in_text(text);
        assert_eq!(result, vec![0, 5]);
    }

    #[test]
    fn conflict_markers_not_at_line_start() {
        let text = "some text <<<<<<< HEAD\nanother line\n";
        let result = find_conflict_markers_in_text(text);
        assert!(result.is_empty());
    }

    #[test]
    fn conflict_markers_bare_marker() {
        // Exactly seven angle brackets with nothing after
        let text = "hello\n<<<<<<<\nworld\n";
        let result = find_conflict_markers_in_text(text);
        assert_eq!(result, vec![1]);
    }
}
