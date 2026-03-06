#[allow(clippy::wildcard_imports)]
use super::*;

pub fn clear_search_tags(buf: &TextBuffer) {
    let start = buf.start_iter();
    let end = buf.end_iter();
    for name in &["search-match", "search-current"] {
        if let Some(tag) = buf.tag_table().lookup(name) {
            buf.remove_tag(&tag, &start, &end);
        }
    }
}

/// Highlight all occurrences of `needle` in `buf`. Returns match count.
pub fn highlight_search_matches(buf: &TextBuffer, needle: &str) -> usize {
    clear_search_tags(buf);
    if needle.is_empty() {
        return 0;
    }
    let mut count = 0;
    let mut iter = buf.start_iter();
    while let Some((match_start, match_end)) =
        iter.forward_search(needle, TextSearchFlags::CASE_INSENSITIVE, None)
    {
        buf.apply_tag_by_name("search-match", &match_start, &match_end);
        count += 1;
        iter = match_end;
    }
    count
}

/// Find the next (or previous) match starting from `from`, without wrapping.
/// When `skip_current` is true, advances one character forward first to avoid
/// re-finding the match at the cursor.
pub fn find_next_match_no_wrap(
    needle: &str,
    from: &gtk4::TextIter,
    forward: bool,
    skip_current: bool,
) -> Option<(gtk4::TextIter, gtk4::TextIter)> {
    if needle.is_empty() {
        return None;
    }
    if forward {
        let mut start = *from;
        if skip_current {
            start.forward_char();
        }
        start.forward_search(needle, TextSearchFlags::CASE_INSENSITIVE, None)
    } else {
        from.backward_search(needle, TextSearchFlags::CASE_INSENSITIVE, None)
    }
}
